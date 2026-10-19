"""Guruh komandiri doirasi (19-bosqich, CLAUDE.md 67-band) — YAGONA joy.

Komandir faqat o'z guruhini ko'radi: guruh `user.cadet.group` dan olinadi, so'rov parametridan emas.
Har bir komandir so'rovi `scoped_cadets(user)` orqali o'tadi (cadet.group == user.cadet.group).
Faqat TASDIQLANGAN sutkalar; kasallik — faqat “kasal, sana–sana” (tavsif, hujjat, sabab, zalyot yo'q).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from functools import wraps

from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _

from . import permissions as perms
from .dashboard import current_duty_date
from .models import Absence, Assignment, Cadet, DutyDay, Penalty, StudyGroup


def commander_group(user) -> StudyGroup:
    """Komandirning guruhi. Akkaunt kursantga bog'lanmagan yoki lavozimi o'zgargan bo'lsa — 403."""
    cadet = getattr(user, "cadet", None)
    if not perms.can(user, "group.view") or cadet is None or not cadet.is_group_commander or not cadet.is_active:
        raise PermissionDenied(_("“Mening guruhim” faqat guruh komandiri uchun."))
    return cadet.group


def scoped_cadets(user):
    """Faqat komandirning guruhi kursantlari (faol). Boshqa guruh id'si bilan so'rov — 404 (mavjudligi oshkor bo'lmaydi)."""
    return Cadet.objects.filter(group=commander_group(user), is_active=True).select_related("group")


def commander_required(view):
    """View dekoratori: ruxsat (group.view) + guruh doirasi; `request.commander_group` ga guruh yoziladi."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        request.commander_group = commander_group(request.user)
        return view(request, *args, **kwargs)

    return perms.role_required("group.view")(wrapper)


@dataclass
class Row:
    cadet: Cadet
    next_duty: Assignment | None = None
    last_duty: Assignment | None = None
    on_duty_now: bool = False
    sick: Absence | None = None  # faqat sanalari ko'rsatiladi
    penalty: object | None = None  # faol zalyot (20-bosqich): “Zalyotchi: 3 tadan 1 tasi o'tildi”

    @property
    def exempt(self) -> bool:
        return self.cadet.duty_exempt


@dataclass
class GroupSummary:
    group: StudyGroup
    today: dt.date
    rows: list[Row] = field(default_factory=list)

    @property
    def on_duty_count(self) -> int:
        return sum(r.on_duty_now for r in self.rows)

    @property
    def sick_count(self) -> int:
        return sum(r.sick is not None for r in self.rows)


def approved(qs):
    return qs.filter(duty_day__status=DutyDay.Status.APPROVED)


def group_summary(user, query: str = "", today: dt.date | None = None) -> GroupSummary:
    today = today or current_duty_date()
    cadets = scoped_cadets(user).order_by("last_name", "first_name")
    if query:
        cadets = cadets.filter(last_name__icontains=query)
    cadets = list(cadets)
    ids = [c.pk for c in cadets]
    data = GroupSummary(group=commander_group(user), today=today, rows=[Row(c) for c in cadets])
    by_id = {r.cadet.pk: r for r in data.rows}
    assignments = approved(Assignment.objects.filter(cadet_id__in=ids)).select_related("duty_day", "post_slot__post")
    for a in assignments.order_by("duty_day__date"):
        row = by_id[a.cadet_id]
        day = a.duty_day.date
        if day == today:
            row.on_duty_now = True
        if day >= today and row.next_duty is None:
            row.next_duty = a
        if day < today:
            row.last_duty = a  # tartib bo'yicha — oxirgisi qoladi
    for ab in Absence.objects.filter(cadet_id__in=ids, reason_type=Absence.Reason.SICK, start_date__lte=today, end_date__gte=today):
        by_id[ab.cadet_id].sick = ab
    from .penalties import with_served

    for p in with_served(Penalty.objects.filter(cadet_id__in=ids, status=Penalty.Status.ACTIVE)):
        by_id[p.cadet_id].penalty = p
    return data


def scoped_cadet(user, pk: int) -> Cadet:
    """Bitta kursant — faqat o'z guruhidan; boshqasi 404."""
    from django.shortcuts import get_object_or_404

    return get_object_or_404(scoped_cadets(user), pk=pk)


def week_table(user, start: dt.date) -> dict:
    """Bir 2-kurs haftasi (yakshanbadan 7 sutka): guruh kursantlari × kunlar, faqat tasdiqlangan sutkalar."""
    days = [start + dt.timedelta(days=i) for i in range(7)]
    cadets = list(scoped_cadets(user).order_by("last_name", "first_name"))
    cells = {
        (a.cadet_id, a.duty_day.date): a
        for a in approved(Assignment.objects.filter(cadet__in=cadets, duty_day__date__range=(days[0], days[-1])))
        .select_related("duty_day", "post_slot__post")
    }
    approved_days = set(
        DutyDay.objects.filter(status=DutyDay.Status.APPROVED, date__range=(days[0], days[-1])).values_list("date", flat=True)
    )
    from .stats import POST_SHORT

    def cell(a):
        return {"a": a, "short": POST_SHORT.get(a.post_slot.post.code, a.post_slot.post.name)} if a else None

    rows = [{"cadet": c, "cells": [cell(cells.get((c.pk, d))) for d in days]} for c in cadets]
    return {"start": start, "days": days, "rows": rows, "approved_days": approved_days,
            "count": [sum(1 for r in rows if r["cells"][i]) for i in range(7)]}


def week_start(day: dt.date) -> dt.date:
    """2-kurs haftasi yakshanbadan boshlanadi (CLAUDE.md 10-bo'lim, 1-band)."""
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)
