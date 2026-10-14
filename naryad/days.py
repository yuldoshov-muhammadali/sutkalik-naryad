"""Sutka bilan ishlash: ko'rinish, muammolar, qo'lda tuzatish, tasdiqlash (7-bosqich).

Algoritmning o'zi (naryad/engine) o'zgarmaydi: almashtirish nomzodlari ham
`pick_cadets` saralash kaliti bilan tartiblanadi. Har o'zgaruvchi amal sutkani
`select_for_update` bilan qulflaydi va `version` ni tekshiradi.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone

from naryad.engine.allocator import History, pick_cadets
from naryad.engine.config import ROTATION_CHAIN
from naryad.engine.models import ROLE_TITLES

from . import services
from .models import (
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    Gender,
    GroupPostAssignment,
    InitialRotation,
    Post,
    PostSlot,
)
from .services import ServiceError, StaleError, check_version

# Qo'lda tuzatish sabablari (CLAUDE.md 6-bo'lim: kasallik, ta'til, sababli holat)
CHANGE_REASONS = [
    ("kasal", "Kasal"),
    ("tatil", "Ta’til"),
    ("sababli", "Sababli"),
    ("boshqa", "Boshqa (izoh majburiy)"),
]
REASON_LABELS = dict(CHANGE_REASONS)
ABSENCE_REASONS = {"kasal", "tatil"}  # bu sabablarda eski kursantga shu sutka uchun Absence yaratiladi


def reason_text(code: str, note: str) -> str:
    note = (note or "").strip()
    if code not in REASON_LABELS:
        raise ServiceError("Sabab tanlanmagan.")
    if code == "boshqa":
        if not note:
            raise ServiceError("“Boshqa” sabab uchun izoh majburiy.")
        return note
    label = REASON_LABELS[code].split(" (")[0]
    return f"{label}: {note}" if note else label


# ---------------------------------------------------------------------------
# Ko'rinish
# ---------------------------------------------------------------------------


@dataclass
class Row:
    slot: PostSlot
    assignment: Assignment | None

    @property
    def cadet(self) -> Cadet | None:
        return self.assignment.cadet if self.assignment else None


@dataclass
class Section:
    post: Post
    group_code: str | None  # o'g'il joyida qaysi guruh berdi; qizlarda None
    rows: list[Row] = field(default_factory=list)

    @property
    def can_swap(self) -> bool:
        return sum(1 for r in self.rows if r.assignment) >= 2 and len({r.slot.role for r in self.rows}) > 1


def sections(duty_day: DutyDay | None) -> list[Section]:
    """Rasmiy shakl tartibida 7 bo'lim (bo'sh o'rinlar bilan)."""
    group_by_post = {}
    by_slot = {}
    if duty_day is not None:
        group_by_post = {g.post_id: g.group.code for g in duty_day.group_posts.select_related("group")}
        by_slot = {
            a.post_slot_id: a
            for a in duty_day.assignments.select_related("cadet__group", "group", "post_slot")
        }
    out = []
    for post in Post.objects.order_by("display_order").prefetch_related("slots"):
        section = Section(post=post, group_code=group_by_post.get(post.pk))
        for slot in sorted(post.slots.all(), key=lambda s: s.position):
            section.rows.append(Row(slot=slot, assignment=by_slot.get(slot.pk)))
        out.append(section)
    return out


@dataclass
class Issue:
    kind: str  # "empty" | "inactive" | "exempt" | "absent"
    text: str
    blocks_approval: bool = True


def day_issues(duty_day: DutyDay) -> list[Issue]:
    """Qoralamadagi joriy muammolar (tasdiqlashga to'sqinlik qiladi)."""
    issues: list[Issue] = []
    filled = {a.post_slot_id: a for a in duty_day.assignments.select_related("cadet__group", "post_slot__post")}
    empty_by_post: dict[Post, int] = {}
    for slot in PostSlot.objects.select_related("post"):
        if slot.pk not in filled:
            empty_by_post[slot.post] = empty_by_post.get(slot.post, 0) + 1
    for post, n in sorted(empty_by_post.items(), key=lambda kv: kv[0].display_order):
        issues.append(Issue("empty", f"{post.name}: {n} ta o‘rin bo‘sh — almashtirish orqali kursant qo‘ying."))
    absences = {
        a.cadet_id: a
        for a in Absence.objects.filter(start_date__lte=duty_day.date, end_date__gte=duty_day.date)
    }
    for a in sorted(filled.values(), key=lambda a: (a.post_slot.post.display_order, a.post_slot.position)):
        if not a.cadet.is_active:
            issues.append(Issue("inactive", f"{a.cadet.short_name} ({a.post_slot.print_label}) faol emas — almashtiring yoki qayta tuzing."))
        elif a.cadet.duty_exempt:
            issues.append(
                Issue("exempt", f"{a.cadet.short_name} ({a.post_slot.print_label}) naryaddan ozod ({a.cadet.duty_position}) — "
                      "almashtiring yoki qayta tuzing.")
            )
        elif a.cadet_id in absences:
            ab = absences[a.cadet_id]
            issues.append(
                Issue("absent", f"{a.cadet.short_name} ({a.post_slot.print_label}) — {ab.get_reason_type_display().lower()} "
                      f"({ab.start_date:%d.%m}–{ab.end_date:%d.%m}). Almashtiring yoki qayta tuzing.")
            )
    return issues


def generation_blocker(day: dt.date) -> str | None:
    """Sutkani tuzib bo'lmasa — sababi (o'zbekcha)."""
    week = DutyWeek.objects.filter(start_date=services.week_start(day)).first()
    if week is None:
        return "Bu sana ochilgan 2-kurs haftasiga tegishli emas."
    try:
        services.check_can_generate(day, week)
    except ServiceError as exc:
        return str(exc)
    if not has_rotation_source():
        return (
            "Tarix ham, boshlang‘ich guruh → joy taqsimoti ham yo‘q — birinchi sutkani tuzib bo‘lmaydi. "
            "Sozlamalarda boshlang‘ich taqsimotni kiriting."
        )
    return None


def has_rotation_source() -> bool:
    return (
        Assignment.objects.filter(duty_day__status=DutyDay.Status.APPROVED, post_slot__post__code__in=ROTATION_CHAIN).exists()
        or InitialRotation.as_mapping() is not None
    )


# ---------------------------------------------------------------------------
# Almashtirish nomzodlari (algoritm kaliti bilan)
# ---------------------------------------------------------------------------


@dataclass
class Candidate:
    cadet: Cadet
    week_count: int | None = None
    total: int | None = None
    post_count: int | None = None
    last_day: dt.date | None = None
    excluded: str = ""  # bo'sh bo'lmasa — nega tanlab bo'lmaydi
    best: bool = False


def candidate_pool(duty_day: DutyDay, slot: PostSlot) -> list[Cadet]:
    qs = Cadet.objects.select_related("group").filter(gender=slot.post.gender)
    if slot.post.gender == Gender.MALE:
        gpa = GroupPostAssignment.objects.filter(duty_day=duty_day, post=slot.post).select_related("group").first()
        if gpa is None:
            return []
        qs = qs.filter(group=gpa.group)
    return list(qs.order_by("last_name"))


def replacement_candidates(duty_day: DutyDay, slot: PostSlot) -> list[Candidate]:
    """Shu o'ringa qo'yish mumkin bo'lgan nomzodlar: eng munosibi birinchi, keyin chiqarilganlar."""
    current = Assignment.objects.filter(duty_day=duty_day, post_slot=slot).first()
    everyone = [c for c in candidate_pool(duty_day, slot) if current is None or c.pk != current.cadet_id]
    exempt = [c for c in everyone if c.duty_exempt]  # algoritm hovuziga kirmaydi, ro'yxat oxirida sababi bilan
    pool = [c for c in everyone if not c.duty_exempt]
    by_id = {c.pk: c for c in pool}
    taken = set(
        Assignment.objects.filter(duty_day=duty_day).exclude(post_slot=slot).values_list("cadet_id", flat=True)
    )
    history = History(services.approved_history(before=duty_day.date), before=duty_day.date)
    pick = pick_cadets(
        [services.to_engine_cadet(c) for c in pool],
        slot.post.code,
        len(pool),
        duty_day.date,
        history,
        services.engine_absences(duty_day.date),
        taken,
    )
    out = []
    for i, s in enumerate(pick.ranking):
        out.append(
            Candidate(by_id[s.cadet_id], s.week_count, s.total, s.post_count, s.last_day, best=(i == 0))
        )
    for cid, reason in pick.excluded.items():
        out.append(Candidate(by_id[cid], excluded=reason))
    for c in exempt:
        out.append(Candidate(c, excluded=exempt_text(c)))
    return out


def exempt_text(cadet: Cadet) -> str:
    return f"naryaddan ozod — {cadet.duty_position}"


def replacement_error(duty_day: DutyDay, slot: PostSlot, cadet: Cadet) -> str | None:
    """Qoidani buzadigan almashtirish bo'lsa — o'zbekcha sababi."""
    post = slot.post
    current = Assignment.objects.filter(duty_day=duty_day, post_slot=slot).first()
    if current is not None and current.cadet_id == cadet.pk:
        return "Bu kursant allaqachon shu o‘rinda."
    if not cadet.is_active:
        return f"{cadet.short_name} faol emas ({cadet.deactivation_reason})."
    if cadet.duty_exempt:
        return f"{cadet.short_name} naryaddan ozod ({cadet.duty_position}) — sutkalik naryadga qo‘yilmaydi."
    if cadet.gender != post.gender:
        if post.gender == Gender.FEMALE:
            return "O‘g‘il bolani Qizlar yotoqxonasiga qo‘yib bo‘lmaydi."
        return "Qizlar faqat Qizlar yotoqxonasida turadi — o‘g‘il bolalar o‘rniga qo‘yib bo‘lmaydi."
    if post.gender == Gender.MALE:
        gpa = GroupPostAssignment.objects.filter(duty_day=duty_day, post=post).select_related("group").first()
        if gpa and gpa.group_id != cadet.group_id:
            return (
                f"{post.name} bu sutkada {gpa.group.code} guruhiga tegishli — boshqa guruhdan "
                f"({cadet.group.code}) kursant qo‘yib bo‘lmaydi."
            )
    other = Assignment.objects.filter(duty_day=duty_day, cadet=cadet).exclude(post_slot=slot).select_related("post_slot").first()
    if other is not None:
        return f"{cadet.short_name} shu sutkada boshqa o‘rinda turibdi: {other.post_slot.print_label}."
    yesterday = duty_day.date - dt.timedelta(days=1)
    if Assignment.objects.filter(duty_day__date=yesterday, cadet=cadet).exists():
        return f"{cadet.short_name} kecha ({yesterday:%d.%m}) naryadda bo‘lgan — ketma-ket ikki sutka turmaydi."
    absence = Absence.objects.filter(cadet=cadet, start_date__lte=duty_day.date, end_date__gte=duty_day.date).first()
    if absence is not None:
        return f"{cadet.short_name} sababli yo‘q: {absence.get_reason_type_display().lower()} ({absence.start_date:%d.%m}–{absence.end_date:%d.%m})."
    return None


# ---------------------------------------------------------------------------
# O'zgartiruvchi amallar (qulf + versiya)
# ---------------------------------------------------------------------------


def lock_draft(date: dt.date, expected_version) -> DutyDay:
    duty_day = DutyDay.objects.select_for_update().filter(date=date).first()
    if duty_day is None:
        raise StaleError("Bu sutka hali tuzilmagan yoki o‘chirilgan — sahifani yangilang.")
    check_version(duty_day, expected_version)
    if duty_day.is_approved:
        raise ServiceError("Sutka tasdiqlangan — o‘zgartirib bo‘lmaydi. Kerak bo‘lsa, admin tasdiqni bekor qiladi.")
    return duty_day


def bump(duty_day: DutyDay) -> None:
    duty_day.version += 1
    duty_day.save(update_fields=["version"])


@transaction.atomic
def replace_cadet(date: dt.date, slot_id: int, new_cadet_id: int, reason_code: str, note: str, user, expected_version) -> Assignment:
    duty_day = lock_draft(date, expected_version)
    reason = reason_text(reason_code, note)
    slot = PostSlot.objects.select_related("post").get(pk=slot_id)
    cadet = Cadet.objects.select_related("group").get(pk=new_cadet_id)
    error = replacement_error(duty_day, slot, cadet)
    if error:
        raise ServiceError(error)

    current = Assignment.objects.filter(duty_day=duty_day, post_slot=slot).select_related("cadet").first()
    old_cadet = current.cadet if current else None
    if current is not None:
        current.delete()
    assignment = Assignment.objects.create(
        duty_day=duty_day, post_slot=slot, cadet=cadet, group=cadet.group, source=Assignment.Source.MANUAL
    )

    if old_cadet is not None and reason_code in ABSENCE_REASONS:
        covered = Absence.objects.filter(cadet=old_cadet, start_date__lte=date, end_date__gte=date).exists()
        if not covered:
            Absence.objects.create(
                cadet=old_cadet, start_date=date, end_date=date, reason_type=reason_code,
                note=f"Qo‘lda almashtirishda avtomatik ({date:%d.%m.%Y} sutkasi)", created_by=user,
            )
            ChangeLog.objects.create(
                action=ChangeLog.Action.ABSENCE_ADD, cadet=old_cadet, user=user,
                details=f"{REASON_LABELS[reason_code].split(' (')[0]}: {date:%d.%m.%Y} (sutkada almashtirilgani uchun avtomatik)",
            )

    ChangeLog.objects.create(
        duty_day=duty_day,
        action=ChangeLog.Action.REPLACE,
        post_slot=slot,
        old_cadet=old_cadet,
        new_cadet=cadet,
        reason=reason,
        reason_code=reason_code,
        user=user,
        details=(f"{old_cadet.short_name} → {cadet.short_name}" if old_cadet else f"Bo‘sh o‘ringa {cadet.short_name}")
        + f" ({slot.print_label})",
    )
    bump(duty_day)
    return assignment


@transaction.atomic
def swap_slots(date: dt.date, slot_a_id: int, slot_b_id: int, reason_code: str, note: str, user, expected_version) -> None:
    """Bitta joy ichida ikki qatordagi kursantlarni o'zaro almashtirish (lavozim almashadi)."""
    duty_day = lock_draft(date, expected_version)
    reason = reason_text(reason_code, note)
    if slot_a_id == slot_b_id:
        raise ServiceError("Ikki xil qatorni tanlang.")
    a = Assignment.objects.select_related("post_slot__post", "cadet", "group").filter(duty_day=duty_day, post_slot_id=slot_a_id).first()
    b = Assignment.objects.select_related("post_slot__post", "cadet", "group").filter(duty_day=duty_day, post_slot_id=slot_b_id).first()
    if a is None or b is None:
        raise ServiceError("Ikkala qatorda ham kursant bo‘lishi kerak.")
    if a.post_slot.post_id != b.post_slot.post_id:
        raise ServiceError("O‘zaro almashtirish faqat bitta joy ichida mumkin.")
    if a.post_slot.role == b.post_slot.role:
        raise ServiceError("Ikkala qatorda lavozim bir xil — almashtirishning ma’nosi yo‘q.")
    slot_a, slot_b = a.post_slot, b.post_slot
    data = [(slot_b, a.cadet, a.group), (slot_a, b.cadet, b.group)]
    Assignment.objects.filter(pk__in=[a.pk, b.pk]).delete()
    for slot, cadet, group in data:
        Assignment.objects.create(duty_day=duty_day, post_slot=slot, cadet=cadet, group=group, source=Assignment.Source.MANUAL)
    ChangeLog.objects.create(
        duty_day=duty_day,
        action=ChangeLog.Action.SWAP,
        post_slot=slot_a,
        old_cadet=a.cadet,
        new_cadet=b.cadet,
        reason=reason,
        reason_code=reason_code,
        user=user,
        details=(
            f"{a.cadet.short_name}: {ROLE_TITLES[slot_a.role]} → {ROLE_TITLES[slot_b.role]}; "
            f"{b.cadet.short_name}: {ROLE_TITLES[slot_b.role]} → {ROLE_TITLES[slot_a.role]} ({slot_a.post.name})"
        ),
    )
    bump(duty_day)


@transaction.atomic
def approve(date: dt.date, user, expected_version) -> DutyDay:
    duty_day = lock_draft(date, expected_version)
    blockers = [i.text for i in day_issues(duty_day) if i.blocks_approval]
    if blockers:
        raise ServiceError("Tasdiqlab bo‘lmaydi: " + " ".join(blockers))
    duty_day.status = DutyDay.Status.APPROVED
    duty_day.approved_by = user
    duty_day.approved_at = timezone.now()
    duty_day.version += 1
    duty_day.save()
    ChangeLog.objects.create(duty_day=duty_day, action=ChangeLog.Action.APPROVE, user=user)
    return duty_day


def reopen_blocker(duty_day: DutyDay) -> str | None:
    later = DutyDay.objects.filter(date__gt=duty_day.date).order_by("date").first()
    if later is not None:
        return f"Keyingi sutka ({later.date:%d.%m.%Y}) allaqachon tuzilgan — avval uni bekor qilish kerak."
    return None


@transaction.atomic
def reopen(date: dt.date, reason: str, user, expected_version) -> DutyDay:
    duty_day = DutyDay.objects.select_for_update().filter(date=date).first()
    if duty_day is None:
        raise StaleError()
    check_version(duty_day, expected_version)
    if not duty_day.is_approved:
        raise ServiceError("Sutka tasdiqlanmagan.")
    if not (reason or "").strip():
        raise ServiceError("Tasdiqni bekor qilish sababi majburiy.")
    blocker = reopen_blocker(duty_day)
    if blocker:
        raise ServiceError(blocker)
    duty_day.status = DutyDay.Status.DRAFT
    duty_day.approved_by = None
    duty_day.approved_at = None
    duty_day.version += 1
    duty_day.save()
    ChangeLog.objects.create(duty_day=duty_day, action=ChangeLog.Action.REOPEN, reason=reason.strip(), user=user)
    return duty_day


@transaction.atomic
def open_week(start_date: dt.date, user, note: str = "") -> DutyWeek:
    from django.core.exceptions import ValidationError

    week = DutyWeek(start_date=start_date, note=note, created_by=user)
    try:
        week.full_clean()
    except ValidationError as exc:
        raise ServiceError(" ".join(m for msgs in exc.message_dict.values() for m in msgs)) from exc
    week.save()
    return week


def delete_blocker(duty_day: DutyDay) -> str | None:
    if duty_day.is_approved:
        return "Tasdiqlangan sutkani o‘chirib bo‘lmaydi — avval tasdiqni bekor qiling."
    later = DutyDay.objects.filter(date__gt=duty_day.date).order_by("date").first()
    if later is not None:
        return f"Faqat eng oxirgi qoralamani o‘chirish mumkin — keyin {later.date:%d.%m.%Y} sutkasi bor."
    return None


@transaction.atomic
def delete_draft(date: dt.date, reason: str, user, expected_version) -> None:
    """Eng oxirgi qoralamani o'chiradi (faqat admin, sabab majburiy). Jurnal saqlanadi (day_date orqali)."""
    duty_day = DutyDay.objects.select_for_update().filter(date=date).first()
    if duty_day is None:
        raise StaleError()
    check_version(duty_day, expected_version)
    blocker = delete_blocker(duty_day)
    if blocker:
        raise ServiceError(blocker)
    if not (reason or "").strip():
        raise ServiceError("Qoralamani o‘chirish sababi majburiy.")
    count = duty_day.assignments.count()
    ChangeLog.objects.create(
        duty_day=None,
        day_date=date,
        action=ChangeLog.Action.DRAFT_DELETE,
        reason=reason.strip(),
        user=user,
        details=f"Qoralama ({count} ta tayinlash) o‘chirildi.",
    )
    duty_day.delete()
