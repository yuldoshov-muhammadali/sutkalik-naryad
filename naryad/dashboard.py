"""Bosh sahifa uchun ma'lumotlar: joriy hafta, sutkalar holati, keyingi qadam."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from django.urls import reverse
from django.utils import timezone

from naryad.engine.config import DUTY_START_TIME, ROTATION_CHAIN

from . import permissions as perms
from .models import Assignment, DutyDay, DutyWeek, InitialRotation

WEEKDAYS = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]


def fmt_day(day: dt.date) -> str:
    return f"{day.day}-{MONTHS[day.month - 1]}"


def current_duty_date(now: dt.datetime | None = None) -> dt.date:
    """Hozir davom etayotgan sutkaning sanasi (sutka 18:00 da boshlanadi)."""
    local = timezone.localtime(now or timezone.now())
    return local.date() if local.time() >= DUTY_START_TIME else local.date() - dt.timedelta(days=1)


def current_week(today: dt.date) -> DutyWeek | None:
    """Joriy 2-kurs haftasi; bo'lmasa — eng yaqin keyingisi; u ham bo'lmasa — oxirgisi."""
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    return (
        DutyWeek.objects.filter(start_date=start).first()
        or DutyWeek.objects.filter(start_date__gt=today).order_by("start_date").first()
        or DutyWeek.objects.order_by("-start_date").first()
    )


@dataclass
class DayRow:
    date: dt.date
    weekday: str
    title: str
    status: str  # "none" | "draft" | "approved"
    status_label: str
    is_current: bool
    warnings: int = 0


@dataclass
class Step:
    label: str
    url: str | None = None
    hint: str = ""
    primary: bool = True

    @property
    def enabled(self) -> bool:
        return self.url is not None


@dataclass
class StaffDashboard:
    today: dt.date
    week: DutyWeek | None
    days: list[DayRow] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)
    notices: list[str] = field(default_factory=list)
    week_state: str = ""  # "current" | "upcoming" | "past" | ""


STATUS_LABELS = {"none": "Tuzilmagan", "draft": "Qoralama", "approved": "Tasdiqlangan"}


def next_generation_date(week: DutyWeek, today: dt.date) -> dt.date | None:
    """Hafta ichida navbatdagi tuziladigan sutka (oraliqsiz; bo'sh haftada — bugundan yoki boshidan)."""
    last = DutyDay.objects.filter(week=week).order_by("-date").values_list("date", flat=True).first()
    if last is None:
        return today if week.contains(today) else week.start_date
    nxt = last + dt.timedelta(days=1)
    return nxt if week.contains(nxt) else None


def staff_dashboard(user, now: dt.datetime | None = None) -> StaffDashboard:
    today = current_duty_date(now)
    week = current_week(today)
    data = StaffDashboard(today=today, week=week)
    is_admin = perms.can(user, "week.open")

    if week is None:
        data.steps.append(Step("2-kurs haftasini ochish", reverse("week_list") if is_admin else None))
        return data

    data.week_state = "current" if week.contains(today) else ("upcoming" if week.start_date > today else "past")
    by_date = {d.date: d for d in week.days.all()}
    for day in week.dates:
        duty = by_date.get(day)
        status = duty.status if duty else "none"
        data.days.append(
            DayRow(
                date=day,
                weekday=WEEKDAYS[day.weekday()],
                title=f"{fmt_day(day)} → {fmt_day(day + dt.timedelta(days=1))}",
                status=status,
                status_label=STATUS_LABELS[status],
                is_current=day == today,
                warnings=len(duty.warnings) if duty else 0,
            )
        )

    draft = DutyDay.objects.filter(status=DutyDay.Status.DRAFT).order_by("date").first()
    if draft is not None:
        day_url = reverse("day_detail", args=[draft.date.isoformat()])
        data.steps.append(Step(f"{fmt_day(draft.date)} qoralamasini ko‘rib chiqish va tasdiqlash", day_url))
        return data

    nxt = next_generation_date(week, today)
    if nxt is not None:
        data.steps.append(Step(f"{fmt_day(nxt)} sutkasi qoralamasini tuzish", reverse("day_detail", args=[nxt.isoformat()])))
        has_history = Assignment.objects.filter(
            duty_day__status=DutyDay.Status.APPROVED, post_slot__post__code__in=ROTATION_CHAIN
        ).exists()
        if not has_history and InitialRotation.as_mapping() is None:
            data.notices.append(
                "Tarix yo‘q va boshlang‘ich guruh → joy taqsimoti kiritilmagan — birinchi sutkani tuzib bo‘lmaydi."
            )
            if is_admin:
                data.steps.append(
                    Step("Boshlang‘ich taqsimotni kiritish", reverse("admin:naryad_setting_change", args=[1]), primary=False)
                )
    else:
        data.notices.append("Bu haftaning barcha 7 sutkasi tuzilgan.")
        data.steps.append(Step("Keyingi 2-kurs haftasini ochish", reverse("week_list") if is_admin else None))
    return data


@dataclass
class CadetDashboard:
    today: dt.date
    cadet: object | None
    next_duty: Assignment | None = None
    recent: list[Assignment] = field(default_factory=list)
    total: int = 0
    this_week: int = 0


def cadet_dashboard(user, now: dt.datetime | None = None) -> CadetDashboard:
    today = current_duty_date(now)
    cadet = getattr(user, "cadet", None)
    data = CadetDashboard(today=today, cadet=cadet)
    if cadet is None:
        return data
    approved = Assignment.objects.filter(cadet=cadet, duty_day__status=DutyDay.Status.APPROVED).select_related(
        "duty_day", "post_slot__post"
    )
    data.next_duty = approved.filter(duty_day__date__gte=today).order_by("duty_day__date").first()
    data.recent = list(approved.filter(duty_day__date__lt=today).order_by("-duty_day__date")[:5])
    data.total = approved.filter(duty_day__date__lte=today).count()
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    data.this_week = approved.filter(duty_day__date__gte=start, duty_day__date__lte=today).count()
    return data
