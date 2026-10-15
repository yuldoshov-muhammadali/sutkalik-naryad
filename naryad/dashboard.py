"""Bosh sahifa uchun ma'lumotlar: joriy hafta, sutkalar holati, keyingi qadam."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from naryad.engine.config import DUTY_START_TIME, ROTATION_CHAIN

from . import i18n
from . import permissions as perms
from .models import Assignment, DutyDay, DutyWeek, InitialRotation, PublishedDuty

# O'zbekcha nomlar (PDF va eski chaqiruvlar uchun); interfeysda — joriy tilda: naryad/i18n.py
WEEKDAYS = i18n.WEEKDAYS["uz"]
MONTHS = i18n.MONTHS["uz"]


def fmt_day(day: dt.date) -> str:
    """14-oktabr / 14 октября / 14 October — joriy tilda."""
    return i18n.day_month(day)


def current_duty_date(now: dt.datetime | None = None) -> dt.date:
    """Hozir davom etayotgan sutkaning sanasi (sutka 18:00 da boshlanadi)."""
    local = timezone.localtime(now or timezone.now())
    return local.date() if local.time() >= DUTY_START_TIME else local.date() - dt.timedelta(days=1)


def clock_context(now: dt.datetime | None = None) -> dict:
    """Bannerdagi jonli soat va joriy sutka paneli uchun boshlang'ich qiymatlar (JS keyin har soniyada yangilaydi).

    `server_now_ms` — server vaqti (epoch, ms): JS faqat farqni hisoblaydi, telefon soati noto'g'ri bo'lsa ham to'g'ri.
    """
    now = now or timezone.now()
    local = timezone.localtime(now)
    duty = current_duty_date(now)
    start = timezone.make_aware(dt.datetime.combine(duty, DUTY_START_TIME), local.tzinfo)
    end = start + dt.timedelta(days=1)
    left = end - local
    hours, minutes = int(left.total_seconds() // 3600), int(left.total_seconds() % 3600 // 60)
    return {
        "server_now_ms": int(now.timestamp() * 1000),
        "time": local.strftime("%H:%M:%S"),
        "date": f"{i18n.weekday(local.date())}, {i18n.long_date(local.date())}",
        "duty_label": f"{fmt_day(duty)} 18:00 → {fmt_day(duty + dt.timedelta(days=1))} 18:00",
        "duty_left": left_text(hours, minutes),
        "duty_pct": round(100 * (local - start).total_seconds() / 86400, 1),
        # JS (static/js/app.js) uchun shablonlar joriy tilda — data- atributlarida beriladi
        "js": {
            **i18n.js_calendar(),
            "left_hm": left_text(1, 1, js=True),
            "left_m": left_text(0, 1, js=True),
        },
    }


def left_text(hours: int, minutes: int, js: bool = False) -> str:
    h, m = ("{h}", "{m}") if js else (hours, minutes)
    if hours:
        return _("Smena almashishiga %(h)s soat %(m)s daqiqa qoldi") % {"h": h, "m": m}
    return _("Smena almashishiga %(m)s daqiqa qoldi") % {"m": m}


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


STATUS_LABELS = {"none": _lazy("Tuzilmagan"), "draft": _lazy("Qoralama"), "approved": _lazy("Tasdiqlangan")}


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
        data.steps.append(Step(_("2-kurs haftasini ochish"), reverse("week_list") if is_admin else None))
        return data

    data.week_state = "current" if week.contains(today) else ("upcoming" if week.start_date > today else "past")
    by_date = {d.date: d for d in week.days.all()}
    for day in week.dates:
        duty = by_date.get(day)
        status = duty.status if duty else "none"
        data.days.append(
            DayRow(
                date=day,
                weekday=i18n.weekday(day),
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
        data.steps.append(Step(_("%(day)s qoralamasini ko‘rib chiqish va tasdiqlash") % {"day": fmt_day(draft.date)}, day_url))
        return data

    nxt = next_generation_date(week, today)
    if nxt is not None:
        data.steps.append(Step(_("%(day)s sutkasi qoralamasini tuzish") % {"day": fmt_day(nxt)}, reverse("day_detail", args=[nxt.isoformat()])))
        has_history = Assignment.objects.filter(
            duty_day__status=DutyDay.Status.APPROVED, post_slot__post__code__in=ROTATION_CHAIN
        ).exists()
        if not has_history and InitialRotation.as_mapping() is None:
            data.notices.append(
                _("Tarix yo‘q va boshlang‘ich guruh → joy taqsimoti kiritilmagan — birinchi sutkani tuzib bo‘lmaydi.")
            )
            if is_admin:
                data.steps.append(
                    Step(_("Boshlang‘ich taqsimotni kiritish"), reverse("admin:naryad_setting_change", args=[1]), primary=False)
                )
    else:
        data.notices.append(_("Bu haftaning barcha 7 sutkasi tuzilgan."))
        data.steps.append(Step(_("Keyingi 2-kurs haftasini ochish"), reverse("week_list") if is_admin else None))
    return data


# ---------------------------------------------------------------------------
# Kursant bosh sahifasi (14-bosqich): faqat o'zining navbatdagi naryadi
# ---------------------------------------------------------------------------


def duty_start(day: dt.date) -> dt.datetime:
    """Sutka boshlanishi (shu sanada 18:00, Toshkent vaqti)."""
    return timezone.make_aware(dt.datetime.combine(day, DUTY_START_TIME), timezone.get_current_timezone())


def _parts(seconds: float) -> tuple[int, int, int]:
    total = max(0, int(seconds // 60))
    return total // 1440, total % 1440 // 60, total % 60


def countdown_text(seconds: float, on_duty: bool) -> str:
    """“Naryadga 21 soat 14 daqiqa qoldi” / “Hozir naryaddasiz, smena almashishiga … qoldi” — joriy tilda."""
    d, h, m = _parts(seconds)
    key = _template_key(d, h, on_duty)
    if on_duty:  # naryad davomida kun ko'rsatilmaydi (ko'pi bilan 24 soat)
        d, h = 0, h + d * 24
    return countdown_templates()[key].format(d=d, h=h, m=m)


def _template_key(d: int, h: int, on_duty: bool) -> str:
    if on_duty:
        return "on_hm" if (d or h) else "on_m"
    return "before_d" if d else ("before_hm" if h else "before_m")


def countdown_templates() -> dict[str, str]:
    """JS (static/js/app.js) ham shu shablonlardan foydalanadi: {d}, {h}, {m} o'rniga son qo'yiladi."""
    t = {"d": "{d}", "h": "{h}", "m": "{m}"}
    return {
        "before_d": _("Naryadga %(d)s kun %(h)s soat qoldi") % t,
        "before_hm": _("Naryadga %(h)s soat %(m)s daqiqa qoldi") % t,
        "before_m": _("Naryadga %(m)s daqiqa qoldi") % t,
        "on_hm": _("Hozir naryaddasiz, smena almashishiga %(h)s soat %(m)s daqiqa qoldi") % t,
        "on_m": _("Hozir naryaddasiz, smena almashishiga %(m)s daqiqa qoldi") % t,
    }


@dataclass
class DutyCard:
    """“Mening navbatdagi naryadim” kartochkasi."""

    assignment: Assignment
    start: dt.datetime
    end: dt.datetime
    on_duty: bool
    when_start: str  # “15-oktabr, chorshanba 18:00”
    when_end: str  # “16-oktabr 18:00”
    countdown: str
    note: str = ""

    @property
    def when(self) -> str:
        return f"{self.when_start} → {self.when_end}"

    @property
    def start_ms(self) -> int:
        return int(self.start.timestamp() * 1000)

    @property
    def end_ms(self) -> int:
        return int(self.end.timestamp() * 1000)


@dataclass
class CadetDashboard:
    today: dt.date
    cadet: object | None
    card: DutyCard | None = None
    cancelled: list[dt.date] = field(default_factory=list)
    total: int = 0
    this_week: int = 0
    penalty: object | None = None  # faol zalyot (15-bosqich): “Jazo naryadlari: 3 tadan 1 tasi o'tildi”
    server_now_ms: int = 0
    templates: dict = field(default_factory=dict)


def duty_card(assignment: Assignment, now: dt.datetime) -> DutyCard:
    day = assignment.duty_day.date
    start = duty_start(day)
    end = start + dt.timedelta(days=1)
    on_duty = start <= now
    note = getattr(assignment.post_slot.post, "prep_note", None)
    return DutyCard(
        assignment=assignment,
        start=start,
        end=end,
        on_duty=on_duty,
        when_start=f"{fmt_day(day)}, {i18n.weekday_inline(day)} 18:00",
        when_end=f"{fmt_day(day + dt.timedelta(days=1))} 18:00",
        countdown=countdown_text(((end if on_duty else start) - now).total_seconds(), on_duty),
        note=note.text(i18n.lang()) if note else "",
    )


def cadet_dashboard(user, now: dt.datetime | None = None) -> CadetDashboard:
    """Kursant faqat o'zining TASDIQLANGAN naryadlarini ko'radi; qoralama hech qachon ko'rinmaydi."""
    now = now or timezone.now()
    today = current_duty_date(now)
    cadet = getattr(user, "cadet", None)
    data = CadetDashboard(today=today, cadet=cadet, server_now_ms=int(now.timestamp() * 1000), templates=countdown_templates())
    if cadet is None:
        return data
    approved = Assignment.objects.filter(cadet=cadet, duty_day__status=DutyDay.Status.APPROVED).select_related(
        "duty_day", "post_slot__post__prep_note", "group"
    )
    nxt = approved.filter(duty_day__date__gte=today).order_by("duty_day__date").first()
    if nxt is not None:
        data.card = duty_card(nxt, now)
    # E'lon qilingan, lekin endi ro'yxatda yo'q (tasdiq bekor qilinib almashtirilgan) — sababsiz xabar
    published = PublishedDuty.objects.filter(cadet=cadet, day_date__gte=today).values_list("day_date", flat=True)
    still_listed = set(
        Assignment.objects.filter(cadet=cadet, duty_day__date__gte=today).values_list("duty_day__date", flat=True)
    )
    data.cancelled = sorted(d for d in published if d not in still_listed)
    normal = approved.filter(kind=Assignment.Kind.NORMAL)  # jazo naryadlari oddiy hisobga kirmaydi
    data.total = normal.filter(duty_day__date__lte=today).count()
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    data.this_week = normal.filter(duty_day__date__gte=start, duty_day__date__lte=today).count()
    from .penalties import active_penalty

    data.penalty = active_penalty(cadet)
    return data
