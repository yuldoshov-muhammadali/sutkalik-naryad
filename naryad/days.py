"""Sutka bilan ishlash: ko'rinish, muammolar, qo'lda tuzatish, tasdiqlash (7-bosqich).

Algoritmning o'zi (naryad/engine) o'zgarmaydi: almashtirish nomzodlari ham
`pick_cadets` saralash kaliti bilan tartiblanadi. Har o'zgaruvchi amal sutkani
`select_for_update` bilan qulflaydi va `version` ni tekshiradi.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from django.db import transaction
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import ngettext

from naryad.engine.allocator import History, pick_cadets
from naryad.engine.config import PENALTY_POSTS, ROTATION_CHAIN
from naryad.engine.models import ROLE_TITLES

from . import penalties, services
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
    Penalty,
    Post,
    PostSlot,
    PublishedDuty,
)
from .services import ServiceError, StaleError, check_version

# Qo'lda tuzatish sabablari (CLAUDE.md 6-bo'lim: kasallik, ta'til, sababli holat)
CHANGE_REASONS = [
    ("kasal", _lazy("Kasal")),
    ("tatil", _lazy("Ta’til")),
    ("sababli", _lazy("Sababli")),
    ("boshqa", _lazy("Boshqa (izoh majburiy)")),
]
REASON_LABELS = dict(CHANGE_REASONS)
ABSENCE_REASONS = {"kasal", "tatil"}  # bu sabablarda eski kursantga shu sutka uchun Absence yaratiladi


def reason_label_uz(code: str) -> str:
    """Jurnalga (ChangeLog) yoziladigan sabab nomi — doim o'zbekcha (saqlanadigan matn)."""
    with translation.override("uz"):
        return str(REASON_LABELS[code]).split(" (")[0]


def reason_text(code: str, note: str) -> str:
    """ChangeLog.reason ga yoziladigan matn — doim o'zbekcha; xatolar esa joriy tilda ko'rsatiladi."""
    note = (note or "").strip()
    if code not in REASON_LABELS:
        raise ServiceError(_("Sabab tanlanmagan."))
    if code == "boshqa":
        if not note:
            raise ServiceError(_("“Boshqa” sabab uchun izoh majburiy."))
        return note
    label = reason_label_uz(code)
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

    @property
    def is_penalty(self) -> bool:
        """Jazo o'rni (zalyotchik, 15-bosqich) — sutka sahifasida “Zalyot” belgisi (PDF’da yo'q)."""
        return bool(self.assignment and self.assignment.kind == Assignment.Kind.PENALTY)


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
    kind: str  # "empty" | "inactive" | "exempt" | "absent" | "sick" | "penalty"
    text: str
    blocks_approval: bool = True
    slot_id: int | None = None  # "sick": sariq ogohlantirishdagi “Almashtirish” tugmasi uchun (17-bosqich)


def day_issues(duty_day: DutyDay) -> list[Issue]:
    """Qoralamadagi joriy muammolar (tasdiqlashga to'sqinlik qiladi)."""
    issues: list[Issue] = []
    filled = {a.post_slot_id: a for a in duty_day.assignments.select_related("cadet__group", "post_slot__post")}
    empty_by_post: dict[Post, int] = {}
    for slot in PostSlot.objects.select_related("post"):
        if slot.pk not in filled:
            empty_by_post[slot.post] = empty_by_post.get(slot.post, 0) + 1
    for post, n in sorted(empty_by_post.items(), key=lambda kv: kv[0].display_order):
        issues.append(Issue("empty", ngettext(
            "%(post)s: %(n)s ta o‘rin bo‘sh — almashtirish orqali kursant qo‘ying.",
            "%(post)s: %(n)s ta o‘rin bo‘sh — almashtirish orqali kursant qo‘ying.",
            n,
        ) % {"post": _(post.name), "n": n}))
    absences = {
        a.cadet_id: a
        for a in Absence.objects.filter(start_date__lte=duty_day.date, end_date__gte=duty_day.date)
    }
    cancelled = set(
        Penalty.objects.filter(
            pk__in=[a.penalty_id for a in filled.values() if a.penalty_id], status=Penalty.Status.CANCELLED
        ).values_list("pk", flat=True)
    )
    for a in sorted(filled.values(), key=lambda a: (a.post_slot.post.display_order, a.post_slot.position)):
        if not a.cadet.is_active:
            issues.append(Issue("inactive", _("%(name)s (%(slot)s) faol emas — almashtiring yoki qayta tuzing.") % {
                "name": a.cadet.short_name, "slot": _(a.post_slot.print_label),
            }))
        elif a.cadet.duty_exempt:
            issues.append(
                Issue("exempt", _("%(name)s (%(slot)s) — %(position)s, naryadga chiqmaydi — almashtiring yoki qayta tuzing.") % {
                    "name": a.cadet.short_name, "slot": _(a.post_slot.print_label), "position": a.cadet.duty_position,
                })
            )
        elif a.kind == Assignment.Kind.PENALTY and a.penalty_id in cancelled:
            # 1.6.0 ochiq savoli (CLAUDE.md 62-band): bekor qilingan zalyot jazo o'rnida qolsa — tasdiqlanmaydi
            issues.append(Issue("penalty", _("%(name)s zalyoti bekor qilingan — jazo o‘rnini almashtiring yoki qayta tuzing.") % {
                "name": a.cadet.short_name,
            }))
        elif a.cadet_id in absences and absences[a.cadet_id].reason_type == Absence.Reason.SICK:
            # 17-bosqich: kasallar ro'yxatidagi kursant — sariq ogohlantirish va “Almashtirish” tugmasi (tasdiqlanmaydi)
            ab = absences[a.cadet_id]
            issues.append(
                Issue("sick", _("%(name)s (%(slot)s) kasallar ro‘yxatida (%(start)s–%(end)s) — “Almashtirish” bilan boshqa kursant qo‘ying.") % {
                    "name": a.cadet.short_name, "slot": _(a.post_slot.print_label),
                    "start": f"{ab.start_date:%d.%m}", "end": f"{ab.end_date:%d.%m}",
                }, slot_id=a.post_slot_id)
            )
        elif a.cadet_id in absences:
            ab = absences[a.cadet_id]
            issues.append(
                Issue("absent", _("%(name)s (%(slot)s) — %(reason)s (%(start)s–%(end)s). Almashtiring yoki qayta tuzing.") % {
                    "name": a.cadet.short_name, "slot": _(a.post_slot.print_label),
                    "reason": ab.get_reason_type_display().lower(),
                    "start": f"{ab.start_date:%d.%m}", "end": f"{ab.end_date:%d.%m}",
                })
            )
    return issues


def approved_sick_notices(duty_day: DutyDay) -> list[str]:
    """Tasdiqlangan sutkada kasallar ro'yxatidagi kursant — faqat admin uchun ogohlantirish, ro'yxat o'zgarmaydi."""
    from .sick import approved_conflict_text

    sick = set(
        Absence.objects.filter(reason_type=Absence.Reason.SICK, start_date__lte=duty_day.date, end_date__gte=duty_day.date)
        .values_list("cadet_id", flat=True)
    )
    rows = duty_day.assignments.filter(cadet_id__in=sick).select_related("cadet").order_by("post_slot__post__display_order")
    return [approved_conflict_text(a.cadet, duty_day.date) for a in rows]


def penalty_notices(duty_day: DutyDay) -> list[str]:
    """Qoralamada jazo o'rniga qo'yilmagan faol zalyotchiklar va sababi — joriy tilda (15-bosqich).

    Algoritm ogohlantirishi (DutyDay.warnings) o'zbekcha saqlanadi; sahifada shu yerda tilga mos qayta tuziladi.
    """
    offenders = penalties.engine_offenders(duty_day.date)
    if not offenders:
        return []
    rows = {a.cadet_id: a for a in duty_day.assignments.all()}
    cadets = Cadet.objects.in_bulk([o.cadet_id for o in offenders])
    yesterday = set(
        Assignment.objects.filter(duty_day__date=duty_day.date - dt.timedelta(days=1)).values_list("cadet_id", flat=True)
    )
    absent = set(
        Absence.objects.filter(start_date__lte=duty_day.date, end_date__gte=duty_day.date).values_list("cadet_id", flat=True)
    )
    out = []
    for o in sorted(offenders, key=lambda o: (o.since, -o.remaining, o.cadet_id)):
        a = rows.get(o.cadet_id)
        if a is not None and a.kind == Assignment.Kind.PENALTY:
            continue
        cadet = cadets[o.cadet_id]
        values = {"name": cadet.short_name}
        if a is not None:
            out.append(_("Zalyotchik %(name)s bugun guruhi bilan oddiy navbatda turibdi (jazo hisobiga o‘tmaydi).") % values)
        elif not cadet.is_active or cadet.duty_exempt:
            out.append(_("Zalyotchik %(name)s faol emas yoki naryadga chiqmaydi (lavozimda) — bugun qo‘yilmadi.") % values)
        elif o.cadet_id in absent:
            out.append(_("Zalyotchik %(name)s sababli holatda bo‘lgani uchun bugun qo‘yilmadi.") % values)
        elif o.cadet_id in yesterday:
            out.append(_("Zalyotchik %(name)s kecha turgani uchun bugun qo‘yilmadi.") % values)
        else:
            out.append(_("Zalyotchik %(name)s: bugun jazo o‘rni qolmadi — keyingi sutkaga qoldi.") % values)
    return out


def generation_blocker(day: dt.date) -> str | None:
    """Sutkani tuzib bo'lmasa — sababi (o'zbekcha)."""
    week = DutyWeek.objects.filter(start_date=services.week_start(day)).first()
    if week is None:
        return _("Bu sana ochilgan 2-kurs haftasiga tegishli emas.")
    try:
        services.check_can_generate(day, week)
    except ServiceError as exc:
        return str(exc)
    if not has_rotation_source():
        return no_rotation_text()
    return None


def no_rotation_text() -> str:
    """Boshlang'ich taqsimot yo'qligi haqidagi to'siq (sahifada Sozlamalar havolasi bilan ko'rsatiladi)."""
    return _(
        "Tarix ham, boshlang‘ich guruh → joy taqsimoti ham yo‘q — birinchi sutkani tuzib bo‘lmaydi. "
        "Sozlamalarda boshlang‘ich taqsimotni kiriting."
    )


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
    offender: bool = False  # faol zalyotchik (jazo o'rniga qo'yiladi)


def candidate_pool(duty_day: DutyDay, slot: PostSlot) -> list[Cadet]:
    qs = Cadet.objects.select_related("group").filter(gender=slot.post.gender)
    if slot.post.gender == Gender.MALE:
        gpa = GroupPostAssignment.objects.filter(duty_day=duty_day, post=slot.post).select_related("group").first()
        if gpa is None:
            return []
        qs = qs.filter(group=gpa.group)
    return list(qs.order_by("last_name"))


def is_penalty_slot(duty_day: DutyDay, slot: PostSlot) -> bool:
    return Assignment.objects.filter(duty_day=duty_day, post_slot=slot, kind=Assignment.Kind.PENALTY).exists()


def replacement_candidates(duty_day: DutyDay, slot: PostSlot) -> list[Candidate]:
    """Shu o'ringa qo'yish mumkin bo'lgan nomzodlar: eng munosibi birinchi, keyin chiqarilganlar.

    Jazo o'rnida (15-bosqich): avval boshqa faol zalyotchiklar, keyin shu joy guruhi kursantlari.
    """
    current = Assignment.objects.filter(duty_day=duty_day, post_slot=slot).first()
    offenders_first = []
    if current is not None and current.kind == Assignment.Kind.PENALTY:
        for p in Penalty.objects.filter(status=Penalty.Status.ACTIVE).exclude(cadet_id=current.cadet_id).select_related(
            "cadet__group"
        ).order_by("order_date", "pk"):
            error = replacement_error(duty_day, slot, p.cadet)
            offenders_first.append(Candidate(p.cadet, excluded=error or "", offender=True))
    everyone = [c for c in candidate_pool(duty_day, slot) if current is None or c.pk != current.cadet_id]
    exempt = [c for c in everyone if c.duty_exempt]  # algoritm hovuziga kirmaydi, ro'yxat oxirida sababi bilan
    pool = [c for c in everyone if not c.duty_exempt]
    by_id = {c.pk: c for c in pool}
    taken = set(
        Assignment.objects.filter(duty_day=duty_day).exclude(post_slot=slot).values_list("cadet_id", flat=True)
    )
    history = History(services.approved_history(before=duty_day.date), before=duty_day.date)
    barred = () if slot.post.code in PENALTY_POSTS else penalties.active_offender_ids()
    pick = pick_cadets(
        [services.to_engine_cadet(c) for c in pool],
        slot.post.code,
        len(pool),
        duty_day.date,
        history,
        services.engine_absences(duty_day.date),
        taken,
        barred,
    )
    out = [c for c in offenders_first if not c.excluded]
    for i, s in enumerate(pick.ranking):
        out.append(
            Candidate(by_id[s.cadet_id], s.week_count, s.total, s.post_count, s.last_day, best=(i == 0))
        )
    sick = {
        ab.cadet_id: ab for ab in Absence.objects.filter(
            reason_type=Absence.Reason.SICK, start_date__lte=duty_day.date, end_date__gte=duty_day.date, cadet_id__in=pick.excluded
        )
    }
    for cid, reason in pick.excluded.items():
        if cid in sick:  # 17-bosqich: kasallar ro'yxatidagi kursant — sababi “Kasal” (tavsifsiz)
            out.append(Candidate(by_id[cid], excluded=sick_text(sick[cid])))
            continue
        out.append(Candidate(by_id[cid], excluded=_(reason)))  # algoritm sababi — joriy tilda (i18n_data.ENGINE_TEXTS)
    for c in exempt:
        out.append(Candidate(c, excluded=exempt_text(c)))
    out += [c for c in offenders_first if c.excluded]
    if out and not out[0].excluded:
        for c in out:
            c.best = False
        out[0].best = True
    return out


def sick_text(absence: Absence) -> str:
    return _("Kasal: %(start)s–%(end)s (kasallar ro‘yxatida).") % {
        "start": f"{absence.start_date:%d.%m}", "end": f"{absence.end_date:%d.%m}",
    }


def exempt_text(cadet: Cadet) -> str:
    return _("%(position)s — naryadga chiqmaydi") % {"position": cadet.duty_position}


def replacement_error(duty_day: DutyDay, slot: PostSlot, cadet: Cadet) -> str | None:
    """Qoidani buzadigan almashtirish bo'lsa — o'zbekcha sababi."""
    post = slot.post
    current = Assignment.objects.filter(duty_day=duty_day, post_slot=slot).first()
    if current is not None and current.cadet_id == cadet.pk:
        return _("Bu kursant allaqachon shu o‘rinda.")
    if not cadet.is_active:
        return _("%(name)s faol emas (%(reason)s).") % {"name": cadet.short_name, "reason": cadet.deactivation_reason}
    if cadet.duty_exempt:
        return _("%(name)s — %(position)s, sutkalik naryadga qo‘yilmaydi.") % {
            "name": cadet.short_name, "position": cadet.duty_position,
        }
    if cadet.gender != post.gender:
        if post.gender == Gender.FEMALE:
            return _("O‘g‘il bolani Qizlar yotoqxonasiga qo‘yib bo‘lmaydi.")
        return _("Qizlar faqat Qizlar yotoqxonasida turadi — o‘g‘il bolalar o‘rniga qo‘yib bo‘lmaydi.")
    is_offender = Penalty.objects.filter(cadet=cadet, status=Penalty.Status.ACTIVE).exists()
    penalty_slot = current is not None and current.kind == Assignment.Kind.PENALTY
    if is_offender and not penalty_slot and post.code not in PENALTY_POSTS:
        return _(
            "%(name)s faol zalyotchik — oddiy navbatda faqat 1-NO‘J yoki 1-Yotoqxonada (o‘z guruhi bilan) turadi, "
            "boshqa joylarga qo‘yilmaydi."
        ) % {"name": cadet.short_name}
    if post.gender == Gender.MALE and not (penalty_slot and is_offender):
        gpa = GroupPostAssignment.objects.filter(duty_day=duty_day, post=post).select_related("group").first()
        if gpa and gpa.group_id != cadet.group_id:
            return _(
                "%(post)s bu sutkada %(group)s guruhiga tegishli — boshqa guruhdan "
                "(%(other)s) kursant qo‘yib bo‘lmaydi."
            ) % {"post": _(post.name), "group": gpa.group.code, "other": cadet.group.code}
    other = Assignment.objects.filter(duty_day=duty_day, cadet=cadet).exclude(post_slot=slot).select_related("post_slot").first()
    if other is not None:
        return _("%(name)s shu sutkada boshqa o‘rinda turibdi: %(slot)s.") % {
            "name": cadet.short_name, "slot": _(other.post_slot.print_label),
        }
    yesterday = duty_day.date - dt.timedelta(days=1)
    if Assignment.objects.filter(duty_day__date=yesterday, cadet=cadet).exists():
        return _("%(name)s kecha (%(day)s) naryadda bo‘lgan — ketma-ket ikki sutka turmaydi.") % {
            "name": cadet.short_name, "day": f"{yesterday:%d.%m}",
        }
    absence = Absence.objects.filter(cadet=cadet, start_date__lte=duty_day.date, end_date__gte=duty_day.date).first()
    if absence is not None and absence.reason_type == Absence.Reason.SICK:
        return sick_text(absence)
    if absence is not None:
        return _("%(name)s sababli yo‘q: %(reason)s (%(start)s–%(end)s).") % {
            "name": cadet.short_name, "reason": absence.get_reason_type_display().lower(),
            "start": f"{absence.start_date:%d.%m}", "end": f"{absence.end_date:%d.%m}",
        }
    return None


# ---------------------------------------------------------------------------
# O'zgartiruvchi amallar (qulf + versiya)
# ---------------------------------------------------------------------------


def lock_draft(date: dt.date, expected_version) -> DutyDay:
    duty_day = DutyDay.objects.select_for_update().filter(date=date).first()
    if duty_day is None:
        raise StaleError(_("Bu sutka hali tuzilmagan yoki o‘chirilgan — sahifani yangilang."))
    check_version(duty_day, expected_version)
    if duty_day.is_approved:
        raise ServiceError(_("Sutka tasdiqlangan — o‘zgartirib bo‘lmaydi. Kerak bo‘lsa, admin tasdiqni bekor qiladi."))
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
    # Jazo o'rniga boshqa faol zalyotchik qo'yilsa — jazo naryadi, shu guruh kursanti qo'yilsa — oddiy naryad
    penalty = None
    if current is not None and current.kind == Assignment.Kind.PENALTY:
        penalty = Penalty.objects.filter(cadet=cadet, status=Penalty.Status.ACTIVE).first()
    if current is not None:
        current.delete()
    assignment = Assignment.objects.create(
        duty_day=duty_day, post_slot=slot, cadet=cadet, group=cadet.group, source=Assignment.Source.MANUAL,
        kind=Assignment.Kind.PENALTY if penalty else Assignment.Kind.NORMAL, penalty=penalty,
    )

    if old_cadet is not None and reason_code in ABSENCE_REASONS:
        covered = Absence.objects.filter(cadet=old_cadet, start_date__lte=date, end_date__gte=date).exists()
        if not covered:
            Absence.objects.create(
                cadet=old_cadet, start_date=date, end_date=date, reason_type=reason_code,
                note=f"Qo‘lda almashtirishda avtomatik ({date:%d.%m.%Y} sutkasi)", created_by=user,  # saqlanadi — o'zbekcha
            )
            ChangeLog.objects.create(
                action=ChangeLog.Action.ABSENCE_ADD, cadet=old_cadet, user=user,
                details=f"{reason_label_uz(reason_code)}: {date:%d.%m.%Y} (sutkada almashtirilgani uchun avtomatik)",
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
        raise ServiceError(_("Ikki xil qatorni tanlang."))
    a = Assignment.objects.select_related("post_slot__post", "cadet", "group").filter(duty_day=duty_day, post_slot_id=slot_a_id).first()
    b = Assignment.objects.select_related("post_slot__post", "cadet", "group").filter(duty_day=duty_day, post_slot_id=slot_b_id).first()
    if a is None or b is None:
        raise ServiceError(_("Ikkala qatorda ham kursant bo‘lishi kerak."))
    if a.post_slot.post_id != b.post_slot.post_id:
        raise ServiceError(_("O‘zaro almashtirish faqat bitta joy ichida mumkin."))
    if a.post_slot.role == b.post_slot.role:
        raise ServiceError(_("Ikkala qatorda lavozim bir xil — almashtirishning ma’nosi yo‘q."))
    if Assignment.Kind.PENALTY in (a.kind, b.kind):
        raise ServiceError(_("Jazo naryadidagi zalyotchik faqat posbon bo‘ladi — uning lavozimini almashtirib bo‘lmaydi."))
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
        raise ServiceError(_("Tasdiqlab bo‘lmaydi: %(issues)s") % {"issues": " ".join(blockers)})
    duty_day.status = DutyDay.Status.APPROVED
    duty_day.approved_by = user
    duty_day.approved_at = timezone.now()
    duty_day.version += 1
    duty_day.save()
    ChangeLog.objects.create(duty_day=duty_day, action=ChangeLog.Action.APPROVE, user=user)
    # Kursantlarga e'lon qilindi: keyin almashtirilganlar “Naryadingiz bekor qilindi” ko'radi (14-bosqich)
    PublishedDuty.objects.bulk_create(
        [PublishedDuty(day_date=duty_day.date, cadet_id=c) for c in duty_day.assignments.values_list("cadet_id", flat=True)],
        ignore_conflicts=True,
    )
    # Jazo naryadi faqat tasdiqlanganda “o'tildi”; soni tugasa — zalyot “bajarildi” (15-bosqich)
    penalties.sync(penalties.day_penalty_ids(duty_day), user)
    return duty_day


def reopen_blocker(duty_day: DutyDay) -> str | None:
    later = DutyDay.objects.filter(date__gt=duty_day.date).order_by("date").first()
    if later is not None:
        return _("Keyingi sutka (%(day)s) allaqachon tuzilgan — avval uni bekor qilish kerak.") % {"day": f"{later.date:%d.%m.%Y}"}
    return None


@transaction.atomic
def reopen(date: dt.date, reason: str, user, expected_version) -> DutyDay:
    duty_day = DutyDay.objects.select_for_update().filter(date=date).first()
    if duty_day is None:
        raise StaleError()
    check_version(duty_day, expected_version)
    if not duty_day.is_approved:
        raise ServiceError(_("Sutka tasdiqlanmagan."))
    if not (reason or "").strip():
        raise ServiceError(_("Tasdiqni bekor qilish sababi majburiy."))
    blocker = reopen_blocker(duty_day)
    if blocker:
        raise ServiceError(blocker)
    duty_day.status = DutyDay.Status.DRAFT
    duty_day.approved_by = None
    duty_day.approved_at = None
    duty_day.version += 1
    duty_day.save()
    ChangeLog.objects.create(duty_day=duty_day, action=ChangeLog.Action.REOPEN, reason=reason.strip(), user=user)
    penalties.sync(penalties.day_penalty_ids(duty_day), user)  # hisob qaytadi
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
        return _("Tasdiqlangan sutkani o‘chirib bo‘lmaydi — avval tasdiqni bekor qiling.")
    later = DutyDay.objects.filter(date__gt=duty_day.date).order_by("date").first()
    if later is not None:
        return _("Faqat eng oxirgi qoralamani o‘chirish mumkin — keyin %(day)s sutkasi bor.") % {"day": f"{later.date:%d.%m.%Y}"}
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
        raise ServiceError(_("Qoralamani o‘chirish sababi majburiy."))
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
