"""Baza ↔ algoritm ko'prigi.

- Bazadagi kursantlar, tasdiqlangan tarix va sababli yo'qliklarni
  `naryad.engine` obyektlariga (Cadet, Record, Absence) aylantiradi.
- `generate_day` natijasini DutyDay + GroupPostAssignment + Assignment sifatida
  qoralama (draft) holatida saqlaydi. Hammasi bitta tranzaksiyada.

Qoidalar (CLAUDE.md 10-bo'lim): sutka faqat admin ochgan 2-kurs haftasi ichida
tuziladi; qoralamalar sutkama-sutka — keyingisi faqat oldingisi tasdiqlangach;
hafta ichida oraliq qoldirilmaydi.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable, Mapping

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from naryad.engine import generate_day
from naryad.engine import models as em
from naryad.engine.allocator import week_start
from naryad.engine.config import ROTATION_CHAIN

from .models import (
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    GroupPostAssignment,
    InitialRotation,
    Penalty,
    Post,
    PostSlot,
    Setting,
    StudyGroup,
)


class ServiceError(Exception):
    """Foydalanuvchiga ko'rsatiladigan xato (joriy tildagi matn bilan; msgid — o'zbekcha)."""


class StaleError(ServiceError):
    """Sutkani boshqa foydalanuvchi shu orada o'zgartirgan (versiya mos emas)."""

    def __init__(self, message: str = ""):
        super().__init__(message or _("Bu sutkani boshqa foydalanuvchi hozirgina o‘zgartirdi — sahifani yangilang va qayta urinib ko‘ring."))


def check_version(duty_day: DutyDay | None, expected_version: int | None) -> None:
    """expected_version: None — tekshirilmaydi; 0 — sutka hali yo'q deb kutilgan."""
    if expected_version is None:
        return
    current = duty_day.version if duty_day is not None else 0
    if int(expected_version) != current:
        raise StaleError()


# ---------------------------------------------------------------------------
# Baza -> engine
# ---------------------------------------------------------------------------


def to_engine_cadet(cadet: Cadet) -> em.Cadet:
    return em.Cadet(
        id=cadet.pk,
        last_name=cadet.last_name,
        first_name=cadet.first_name,
        patronymic=cadet.patronymic,
        group=cadet.group.code,
        gender=cadet.gender,
        active=cadet.is_active,
        short_name=cadet.short_name,
    )


def engine_cadets() -> list[em.Cadet]:
    """Nomzodlar hovuzi: barcha kursantlar (faol emaslari ham — algoritm ularni o'zi chiqarib tashlaydi),
    lavozimdagilardan tashqari (CLAUDE.md 4-bo'lim). Algoritm qoidalari o'zgarmaydi — ular hovuzga kirmaydi."""
    qs = Cadet.objects.select_related("group").filter(duty_exempt=False).order_by("pk")
    return [to_engine_cadet(c) for c in qs]


def approved_history(before: dt.date | None = None) -> list[em.Record]:
    """Faqat tasdiqlangan sutkalardagi tayinlashlar — algoritm uchun tarix."""
    qs = Assignment.objects.filter(duty_day__status=DutyDay.Status.APPROVED).select_related(
        "duty_day", "post_slot__post", "group"
    )
    if before is not None:
        qs = qs.filter(duty_day__date__lt=before)
    return [
        em.Record(
            day=a.duty_day.date,
            cadet_id=a.cadet_id,
            post=a.post_slot.post.code,
            role=a.post_slot.role,
            group=a.group.code,
            position=a.post_slot.position,
            kind=a.kind,
        )
        for a in qs.order_by("duty_day__date", "post_slot__post__display_order", "post_slot__position")
    ]


def engine_absences(day: dt.date) -> list[em.Absence]:
    """Shu sutkani qamrab olgan sababli yo'qliklar."""
    qs = Absence.objects.filter(start_date__lte=day, end_date__gte=day)
    return [em.Absence(cadet_id=a.cadet_id, start=a.start_date, end=a.end_date, reason=a.reason_type) for a in qs]


def stored_rotation(duty_day: DutyDay | None) -> dict[str, str] | None:
    """Sutka uchun admin qo'lda kiritgan guruh → joy taqsimoti (6 ta bo'lsa)."""
    if duty_day is None:
        return None
    rows = {g.post.code: g.group.code for g in duty_day.group_posts.select_related("post", "group")}
    return rows if set(rows) == set(ROTATION_CHAIN) else None


# ---------------------------------------------------------------------------
# Tekshiruvlar
# ---------------------------------------------------------------------------


def find_week(day: dt.date, *, lock: bool = False) -> DutyWeek:
    qs = DutyWeek.objects.select_for_update() if lock else DutyWeek.objects
    week = qs.filter(start_date=week_start(day)).first()
    if week is None:
        raise ServiceError(
            _(
                "%(day)s sutkasi ochilgan 2-kurs haftasiga tegishli emas. "
                "Avval admin %(start)s (yakshanba) dan boshlanadigan haftani ochishi kerak."
            ) % {"day": f"{day:%d.%m.%Y}", "start": f"{week_start(day):%d.%m.%Y}"}
        )
    return week


def check_can_generate(day: dt.date, week: DutyWeek) -> DutyDay | None:
    """Sutkama-sutka qoidasi. Mavjud qoralamani (qayta tuzish uchun) qaytaradi."""
    existing = DutyDay.objects.filter(date=day).first()
    if existing is not None and existing.is_approved:
        raise ServiceError(
            _("%(day)s sutkasi allaqachon tasdiqlangan. O‘zgartirish uchun admin uni qayta ochishi kerak.") % {"day": f"{day:%d.%m.%Y}"}
        )

    other_draft = DutyDay.objects.filter(status=DutyDay.Status.DRAFT).exclude(date=day).order_by("date").first()
    if other_draft is not None:
        raise ServiceError(
            _("Avval %(day)s sutkasi qoralamasini tasdiqlang (sutkalar ketma-ket tuziladi).") % {"day": f"{other_draft.date:%d.%m.%Y}"}
        )

    later = DutyDay.objects.filter(status=DutyDay.Status.APPROVED, date__gt=day).order_by("date").first()
    if later is not None:
        raise ServiceError(
            _("%(day)s sutkasi allaqachon tasdiqlangan — undan oldingi sanaga qoralama tuzib bo‘lmaydi.") % {"day": f"{later.date:%d.%m.%Y}"}
        )

    # Haftada sutkalar oraliq qoldirmay ketma-ket tuziladi. Platformagacha bo'lgan
    # (bazada yozuvi yo'q) sutkalar to'siq emas — CLAUDE.md 10-bo'lim, 14-band.
    last_in_week = (
        DutyDay.objects.filter(week=week, date__lt=day).order_by("-date").values_list("date", flat=True).first()
    )
    if last_in_week is not None and last_in_week != day - dt.timedelta(days=1):
        missing = [last_in_week + dt.timedelta(days=i) for i in range(1, (day - last_in_week).days)]
        raise ServiceError(
            _("Haftaning oldingi sutkalari tuzilmagan/tasdiqlanmagan: %(days)s.") % {"days": ", ".join(f"{d:%d.%m}" for d in missing)}
        )
    return existing


# ---------------------------------------------------------------------------
# Engine -> baza
# ---------------------------------------------------------------------------


@transaction.atomic
def save_day_result(
    result: em.DayResult,
    week: DutyWeek,
    user=None,
    existing: DutyDay | None = None,
    details: str = "",
) -> DutyDay:
    """DayResult ni qoralama sutka sifatida saqlaydi (mavjud qoralama qayta yoziladi)."""
    posts = {p.code: p for p in Post.objects.all()}
    slots = {(s.post.code, s.position): s for s in PostSlot.objects.select_related("post")}
    groups = {g.code: g for g in StudyGroup.objects.all()}
    cadets = Cadet.objects.in_bulk([a.cadet_id for a in result.filled])
    penalty_ids = {
        p.cadet_id: p.pk
        for p in Penalty.objects.filter(
            status=Penalty.Status.ACTIVE, cadet_id__in=[a.cadet_id for a in result.filled if a.kind == em.KIND_PENALTY]
        )
    }

    duty_day = existing or DutyDay(week=week, date=result.day)
    duty_day.week = week
    duty_day.status = DutyDay.Status.DRAFT
    duty_day.warnings = list(result.warnings)
    duty_day.generated_by = user
    duty_day.generated_at = timezone.now()
    duty_day.approved_by = None
    duty_day.approved_at = None
    if existing is not None:
        duty_day.version = existing.version + 1
    duty_day.full_clean()
    duty_day.save()

    duty_day.assignments.all().delete()
    duty_day.group_posts.all().delete()

    GroupPostAssignment.objects.bulk_create(
        GroupPostAssignment(duty_day=duty_day, post=posts[code], group=groups[group])
        for code, group in result.group_by_post.items()
    )
    Assignment.objects.bulk_create(
        Assignment(
            duty_day=duty_day,
            post_slot=slots[(a.slot.post, a.slot.position)],
            cadet=cadets[a.cadet_id],
            group=groups[a.group],
            source=Assignment.Source.AUTO,
            kind=a.kind,
            penalty_id=penalty_ids[a.cadet_id] if a.kind == em.KIND_PENALTY else None,
        )
        for a in result.filled
    )
    ChangeLog.objects.create(duty_day=duty_day, action=ChangeLog.Action.GENERATE, user=user, details=details)
    return duty_day


@transaction.atomic
def generate_draft(
    day: dt.date,
    user=None,
    initial_rotation: Mapping[str, str] | None = None,
    absences: Iterable[em.Absence] | None = None,
    expected_version: int | None = None,
) -> DutyDay:
    """Bitta sutka qoralamasini tuzadi va saqlaydi.

    Tarixda o'g'il bolalar naryadi bo'lmasa (eng birinchi sutka), guruh → joy
    taqsimoti `initial_rotation` dan yoki admin shu sutkaga qo'lda kiritgan
    GroupPostAssignment yozuvlaridan olinadi.
    """
    week = find_week(day, lock=True)
    existing = check_can_generate(day, week)
    if existing is not None:
        existing = DutyDay.objects.select_for_update().get(pk=existing.pk)
    check_version(existing, expected_version)
    rotation = dict(initial_rotation) if initial_rotation else stored_rotation(existing)
    history = approved_history(before=day)
    if rotation is None:
        rotation = InitialRotation.as_mapping()
    if rotation is None and not any(r.post in ROTATION_CHAIN for r in history):
        raise ServiceError(
            _(
                "Tarix bo‘sh: birinchi sutka uchun admin guruhlarning qaysi joydan boshlashini kiritishi kerak "
                "(Sozlamalar → Boshlang‘ich taqsimot: 6 guruh × 6 joy, har biri bir marta) "
                "yoki o‘tgan sutkalarni import_history buyrug‘i bilan kiritishi kerak."
            )
        )
    from .penalties import engine_offenders  # aylana importdan qochish

    setting = Setting.load()
    result = generate_day(
        day,
        engine_cadets(),
        history,
        engine_absences(day) if absences is None else list(absences),
        initial_rotation=rotation,
        offenders=engine_offenders(day),
        penalty_per_post=setting.penalty_per_post,
        rotation=setting.post_rotation(),  # 21-bosqich: o'chiq bo'lsa None — eski tartib
    )
    # ChangeLog.details — saqlanadigan matn, doim o'zbekcha (tarjima qilinmaydi)
    details = "Qayta tuzildi: avvalgi qoralama almashtirildi." if existing is not None else ""
    return save_day_result(result, week, user=user, existing=existing, details=details)
