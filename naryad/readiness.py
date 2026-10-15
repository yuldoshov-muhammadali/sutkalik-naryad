"""Ertangi ro'yxat bir kun oldin tayyor bo'lsin (14-bosqich, CLAUDE.md 60-band).

Qoida: D sanadagi sutka (D kuni 18:00 da boshlanadi) kamida `Setting.approval_lead_hours` soat oldin
(standart 24 — D−1 kuni 18:00 gacha) tasdiqlangan bo'lishi kerak. Admin bosh sahifasida banner:
sariq — muddat hali o'tmagan, qizil — o'tdi, yashil — ertangi sutka tasdiqlangan.
Banner faqat 2-kurs haftasiga kiradigan sutka uchun chiqadi (hafta boshlanishidan oldingi kuni ham —
yakshanba sutkasi uchun shanba). Sutkalar ketma-ketligi qoidasi o'zgarmaydi.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from .dashboard import duty_start, fmt_day
from .models import DutyDay, DutyWeek, Setting

YELLOW, RED, GREEN = "yellow", "red", "green"


@dataclass
class ApprovalBanner:
    level: str  # yellow | red | green
    day: dt.date
    text: str
    action_label: str
    action_url: str


def approval_deadline(day: dt.date, lead_hours: int) -> dt.datetime:
    return duty_start(day) - dt.timedelta(hours=lead_hours)


def _week_start(day: dt.date) -> dt.date:
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)  # shu sanagacha bo'lgan yakshanba


def _left_text(seconds: float) -> str:
    minutes = max(1, int(seconds // 60))
    h, m = divmod(minutes, 60)
    if h and m:
        return _("%(h)s soat %(m)s daqiqa") % {"h": h, "m": m}
    if h:
        return _("%(h)s soat") % {"h": h}
    return _("%(m)s daqiqa") % {"m": m}


def _deadline_text(deadline: dt.datetime, now: dt.datetime) -> str:
    """“bugun 18:00 gacha, 3 soat qoldi” — joriy tilda."""
    local, today = timezone.localtime(deadline), timezone.localtime(now).date()
    values = {"time": local.strftime("%H:%M"), "date": fmt_day(local.date()), "left": _left_text((deadline - now).total_seconds())}
    if local.date() == today:
        return _("Muddat: bugun %(time)s gacha, %(left)s qoldi.") % values
    if local.date() == today + dt.timedelta(days=1):
        return _("Muddat: ertaga %(time)s gacha, %(left)s qoldi.") % values
    return _("Muddat: %(date)s %(time)s gacha, %(left)s qoldi.") % values


def approval_banner(now: dt.datetime | None = None) -> ApprovalBanner | None:
    now = now or timezone.now()
    today = timezone.localtime(now).date()
    tomorrow = today + dt.timedelta(days=1)
    lead = Setting.load().approval_lead_hours
    days = {d.date: d for d in DutyDay.objects.filter(date__in=[today, tomorrow])}
    weeks = set(
        DutyWeek.objects.filter(start_date__in={_week_start(today), _week_start(tomorrow)}).values_list("start_date", flat=True)
    )

    def _in_week(day: dt.date) -> bool:
        return _week_start(day) in weeks

    def action(day: dt.date) -> tuple[str, str]:
        url = reverse("day_detail", args=[day.isoformat()])
        return (_("Ochish") if day in days else _("Tuzish")), url

    # Bugun 18:00 da boshlanadigan sutka hali tasdiqlanmagan va muddati o'tgan — eng shoshilinch
    if duty_start(today) > now and _in_week(today):
        duty = days.get(today)
        if not (duty and duty.is_approved) and approval_deadline(today, lead) <= now:
            text = _("Bugungi sutka (%(day)s) hali tasdiqlanmagan. Muddat o‘tdi, kursantlar hali bilmaydi.") % {"day": fmt_day(today)}
            return ApprovalBanner(RED, today, text, *action(today))

    if not _in_week(tomorrow):
        return None
    duty = days.get(tomorrow)
    label = {"day": fmt_day(tomorrow)}
    if duty and duty.is_approved:
        return ApprovalBanner(
            GREEN, tomorrow, _("Ertangi ro‘yxat (%(day)s) tayyor, kursantlarga ko‘rinmoqda.") % label, *action(tomorrow)
        )
    deadline = approval_deadline(tomorrow, lead)
    if deadline > now:
        text = _("Ertangi sutka (%(day)s) hali tasdiqlanmagan.") % label + " " + _deadline_text(deadline, now)
        return ApprovalBanner(YELLOW, tomorrow, text, *action(tomorrow))
    text = _("Ertangi sutka (%(day)s) hali tasdiqlanmagan. Muddat o‘tdi, kursantlar hali bilmaydi.") % label
    return ApprovalBanner(RED, tomorrow, text, *action(tomorrow))
