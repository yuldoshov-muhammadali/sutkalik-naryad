"""Haftalar, sutka (tuzish, tuzatish, tasdiqlash), jurnal va sababli holatlar sahifalari (7-bosqich)."""

from __future__ import annotations

import datetime as dt

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext as _
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from . import absences as absence_service
from . import days, i18n, services
from . import permissions as perms
from .dashboard import current_duty_date, fmt_day
from .models import Absence, ChangeLog, DutyDay, DutyWeek, PostSlot


def parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise Http404("Sana noto‘g‘ri") from exc


def day_url(date: dt.date) -> str:
    return reverse("day_detail", args=[date.isoformat()])


def htmx_redirect(request, url: str):
    if request.headers.get("HX-Request"):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = url
        return response
    return redirect(url)


# ---------------------------------------------------------------------------
# Haftalar
# ---------------------------------------------------------------------------


def week_rows(week: DutyWeek):
    by_date = {d.date: d for d in week.days.all()}
    today = current_duty_date()
    return [
        {
            "date": d,
            "weekday": i18n.weekday(d),
            "title": f"{fmt_day(d)} 18:00 → {fmt_day(d + dt.timedelta(days=1))} 18:00",
            "status": by_date[d].status if d in by_date else "none",
            "is_current": d == today,
        }
        for d in week.dates
    ]


@perms.role_required("week.view")
def week_list(request):
    weeks = DutyWeek.objects.prefetch_related("days").order_by("-start_date")
    context = {
        "weeks": [
            {"week": w, "days": (rows := week_rows(w)), "has_days": any(r["status"] != "none" for r in rows)} for w in weeks
        ],
        "needs_rotation": not days.has_rotation_source(),
        "suggested": suggest_next_sunday(),
    }
    return render(request, "naryad/days/weeks.html", context)


def suggest_next_sunday() -> dt.date:
    last = DutyWeek.objects.order_by("-start_date").first()
    today = current_duty_date()
    base = last.start_date + dt.timedelta(days=7) if last else today
    base = max(base, today - dt.timedelta(days=6))
    return base + dt.timedelta(days=(6 - base.weekday()) % 7)


@perms.role_required("week.open")
def week_preview(request):
    """HTMX: tanlangan yakshanba uchun 7 sutka ko'rinishi."""
    try:
        start = dt.date.fromisoformat(request.GET.get("start_date", ""))
    except ValueError:
        return HttpResponse(format_html('<p class="text-sm text-slate-500">{}</p>', _("Sanani tanlang.")))
    if start.isoweekday() != 7:
        return HttpResponse(format_html(
            '<p class="text-sm font-medium text-red-700">{}</p>',
            _("Tanlangan sana yakshanba emas — hafta faqat yakshanba 18:00 da boshlanadi."),
        ))
    rows = [
        format_html(
            "<li>{} · {}: {} 18:00 → {} 18:00</li>",
            _("%(n)s-sutka") % {"n": i + 1},
            i18n.weekday(start + dt.timedelta(days=i)),
            fmt_day(start + dt.timedelta(days=i)),
            fmt_day(start + dt.timedelta(days=i + 1)),
        )
        for i in range(7)
    ]
    return HttpResponse('<ol class="space-y-0.5 text-sm text-slate-700">' + "".join(rows) + "</ol>")


@require_POST
@perms.role_required("week.open")
def week_open(request):
    try:
        start = dt.date.fromisoformat(request.POST.get("start_date", ""))
        week = days.open_week(start, request.user, request.POST.get("note", "").strip()[:200])
    except ValueError:
        messages.error(request, _("Sana noto‘g‘ri."))
    except services.ServiceError as exc:
        messages.error(request, _("Hafta ochilmadi: %(error)s") % {"error": exc})
    else:
        messages.success(request, _("2-kurs haftasi ochildi: %(week)s.") % {"week": week})
    return redirect("week_list")


# ---------------------------------------------------------------------------
# Sutka
# ---------------------------------------------------------------------------


@perms.role_required("day.view_approved")
def day_detail(request, date):
    date = parse_date(date)
    duty_day = DutyDay.objects.filter(date=date).select_related("week", "approved_by", "generated_by").first()
    can_draft = perms.can(request.user, "day.view_draft")
    if not can_draft and (duty_day is None or not duty_day.is_approved):
        raise Http404("Bu sutka hali tasdiqlanmagan.")
    week = duty_day.week if duty_day else DutyWeek.objects.filter(start_date=services.week_start(date)).first()
    if week is None and can_draft:
        messages.warning(request, _("%(day)s ochilgan 2-kurs haftasiga tegishli emas.") % {"day": f"{date:%d.%m.%Y}"})
        return redirect("week_list")

    context = {
        "date": date,
        "title": _("%(start)s kunidan %(end)s kuniga") % {"start": fmt_day(date), "end": fmt_day(date + dt.timedelta(days=1))},
        "weekday": i18n.weekday(date),
        "duty_day": duty_day,
        "week": week,
        "sections": days.sections(duty_day),
        "prev_date": date - dt.timedelta(days=1),
        "next_date": date + dt.timedelta(days=1),
        "editable": duty_day is not None and not duty_day.is_approved and perms.can(request.user, "day.edit"),
    }
    if can_draft:
        all_issues = days.day_issues(duty_day) if duty_day and not duty_day.is_approved else []
        context["issues"] = [i for i in all_issues if i.blocks_approval]
        # tasdiqlashga to'sqinlik qilmaydigan eslatmalar (zalyotchiklar, 15-bosqich)
        context["notes"] = [i.text for i in all_issues if not i.blocks_approval] + (
            days.penalty_notices(duty_day) if duty_day and not duty_day.is_approved else []
        )
        context["generation_blocker"] = days.generation_blocker(date) if duty_day is None or not duty_day.is_approved else None
        # Sozlamalar havolasi faqat boshlang'ich taqsimot yo'qligi sababli bo'lsa (matn tilga bog'liq emas)
        context["blocker_needs_settings"] = context["generation_blocker"] == days.no_rotation_text()
        context["reopen_blocker"] = days.reopen_blocker(duty_day) if duty_day and duty_day.is_approved else None
        context["delete_blocker"] = days.delete_blocker(duty_day) if duty_day and not duty_day.is_approved else None
        context["has_log"] = ChangeLog.objects.filter(day_date=date).exists()
    return render(request, "naryad/days/day.html", context)


@require_POST
@perms.role_required("day.generate")
def day_generate(request, date):
    date = parse_date(date)
    try:
        duty_day = services.generate_draft(date, request.user, expected_version=request.POST.get("version"))
    except services.ServiceError as exc:
        messages.error(request, str(exc))
    else:
        regenerated = duty_day.version > 1
        messages.success(request, _("Qoralama qayta tuzildi (avvalgisi almashtirildi).") if regenerated else _("Qoralama tuzildi."))
    return redirect(day_url(date))


@perms.role_required("day.edit")
def day_replace(request, date, slot_id):
    date = parse_date(date)
    duty_day = get_object_or_404(DutyDay, date=date)
    slot = get_object_or_404(PostSlot.objects.select_related("post"), pk=slot_id)
    error = None
    if request.method == "POST":
        try:
            new_cadet = int(request.POST.get("cadet") or 0)
            if not new_cadet:
                raise services.ServiceError(_("Kursantni tanlang."))
            days.replace_cadet(
                date, slot.pk, new_cadet, request.POST.get("reason", ""), request.POST.get("note", ""),
                request.user, request.POST.get("version"),
            )
        except services.ServiceError as exc:
            error = str(exc)
            duty_day.refresh_from_db()
        else:
            messages.success(request, _("%(slot)s: almashtirildi.") % {"slot": _(slot.print_label)})
            return htmx_redirect(request, day_url(date))
    current = duty_day.assignments.filter(post_slot=slot).select_related("cadet").first()
    context = {
        "duty_day": duty_day,
        "slot": slot,
        "current": current,
        "candidates": days.replacement_candidates(duty_day, slot) if not duty_day.is_approved else [],
        "reasons": days.CHANGE_REASONS,
        "error": error,
        "posted": request.POST if request.method == "POST" else {},
        "back": day_url(date),
    }
    template = "naryad/days/_replace.html" if request.headers.get("HX-Request") else "naryad/days/replace_page.html"
    return render(request, template, context)


@perms.role_required("day.edit")
def day_swap(request, date, post_id):
    date = parse_date(date)
    duty_day = get_object_or_404(DutyDay, date=date)
    section = next((s for s in days.sections(duty_day) if s.post.pk == int(post_id)), None)
    if section is None:
        raise Http404
    error = None
    if request.method == "POST":
        try:
            days.swap_slots(
                date, int(request.POST.get("slot_a") or 0), int(request.POST.get("slot_b") or 0),
                request.POST.get("reason", ""), request.POST.get("note", ""), request.user, request.POST.get("version"),
            )
        except (services.ServiceError, ValueError) as exc:
            error = str(exc)
            duty_day.refresh_from_db()
        else:
            messages.success(request, _("%(post)s: lavozimlar almashtirildi.") % {"post": _(section.post.name)})
            return htmx_redirect(request, day_url(date))
    context = {
        "duty_day": duty_day, "section": section, "reasons": days.CHANGE_REASONS, "error": error,
        "posted": request.POST if request.method == "POST" else {}, "back": day_url(date),
    }
    template = "naryad/days/_swap.html" if request.headers.get("HX-Request") else "naryad/days/swap_page.html"
    return render(request, template, context)


@require_POST
@perms.role_required("day.approve")
def day_approve(request, date):
    date = parse_date(date)
    try:
        days.approve(date, request.user, request.POST.get("version"))
    except services.ServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, _("%(day)s sutkasi tasdiqlandi. Endi uni kursantlar ham ko‘radi.") % {"day": f"{date:%d.%m.%Y}"})
    return redirect(day_url(date))


@require_POST
@perms.role_required("day.reopen")
def day_reopen(request, date):
    date = parse_date(date)
    try:
        days.reopen(date, request.POST.get("reason", ""), request.user, request.POST.get("version"))
    except services.ServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.warning(request, _("%(day)s sutkasining tasdig‘i bekor qilindi — qoralama holatida.") % {"day": f"{date:%d.%m.%Y}"})
    return redirect(day_url(date))


@require_POST
@perms.role_required("day.generate")
def day_delete(request, date):
    date = parse_date(date)
    try:
        days.delete_draft(date, request.POST.get("reason", ""), request.user, request.POST.get("version"))
    except services.ServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.warning(request, _("%(day)s qoralamasi o‘chirildi (jurnalda saqlandi).") % {"day": f"{date:%d.%m.%Y}"})
    return redirect(day_url(date))


@perms.role_required("day.view_draft")
def day_log(request, date):
    date = parse_date(date)
    duty_day = DutyDay.objects.filter(date=date).first()
    entries = (
        ChangeLog.objects.filter(day_date=date)
        .select_related("user", "post_slot", "old_cadet", "new_cadet")
        .order_by("created_at", "id")
    )
    if duty_day is None and not entries.exists():
        raise Http404("Bu sutka bo‘yicha jurnal yo‘q.")
    return render(request, "naryad/days/log.html", {"duty_day": duty_day, "entries": entries, "date": date})


@perms.role_required("day.view_approved")
def approved_days(request):
    qs = DutyDay.objects.filter(status=DutyDay.Status.APPROVED).order_by("-date")[:60]
    rows = [{"day": d, "title": f"{fmt_day(d.date)} → {fmt_day(d.date + dt.timedelta(days=1))}", "weekday": i18n.weekday(d.date)} for d in qs]
    return render(request, "naryad/days/approved.html", {"rows": rows})


# ---------------------------------------------------------------------------
# Sababli holatlar
# ---------------------------------------------------------------------------


@perms.role_required("absence.manage")
def absence_list(request):
    today = current_duty_date()
    form = absence_service.AbsenceForm(request.POST or None, initial={"start_date": today, "end_date": today})
    if request.method == "POST" and form.is_valid():
        absence = absence_service.add(form, request.user)
        messages.success(request, _("Kiritildi: %(name)s — %(reason)s %(start)s–%(end)s.") % {
            "name": absence.cadet.short_name, "reason": absence.get_reason_type_display().lower(),
            "start": f"{absence.start_date:%d.%m}", "end": f"{absence.end_date:%d.%m}",
        })
        return redirect("absence_list")
    qs = Absence.objects.select_related("cadet__group", "created_by")
    active = qs.filter(start_date__lte=today, end_date__gte=today).order_by("end_date")
    upcoming = qs.filter(start_date__gt=today).order_by("start_date")
    past = qs.filter(end_date__lt=today).order_by("-end_date")[:30]
    return render(request, "naryad/days/absences.html", {
        "form": form, "active": active, "upcoming": upcoming, "past": past, "today": today,
    })


@require_POST
@perms.role_required("absence.manage")
def absence_end(request, pk):
    absence = get_object_or_404(Absence, pk=pk)
    form = absence_service.EndDateForm(absence, request.POST)
    if form.is_valid():
        absence_service.change_end(absence, form.cleaned_data["end_date"], request.user)
        messages.success(request, _("%(name)s: tugash sanasi %(day)s ga o‘zgartirildi.") % {
            "name": absence.cadet.short_name, "day": f"{absence.end_date:%d.%m.%Y}",
        })
    else:
        messages.error(request, "; ".join(e for errs in form.errors.values() for e in errs))
    return redirect("absence_list")


@require_POST
@perms.role_required("absence.manage")
def absence_delete(request, pk):
    absence = get_object_or_404(Absence, pk=pk)
    if not absence_service.can_delete(absence):
        raise PermissionDenied("Boshlangan (tarixi bor) yozuv o‘chirilmaydi — tugash sanasini o‘zgartiring.")
    absence_service.delete(absence, request.user)
    messages.success(request, _("Yozuv o‘chirildi."))
    return redirect("absence_list")


# ---------------------------------------------------------------------------
# PDF va chop etish (8-bosqich)
# ---------------------------------------------------------------------------


def _pdf_response(content: bytes, filename: str, inline: bool) -> HttpResponse:
    response = HttpResponse(content, content_type="application/pdf")
    disposition = "inline" if inline else "attachment"
    response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response


def _visible_day(request, date: dt.date) -> DutyDay:
    """Tasdiqlangan sutka — hamma rol; qoralama — faqat admin (day.view_draft)."""
    duty_day = DutyDay.objects.filter(date=date).first()
    if duty_day is None:
        raise Http404("Bu sutka hali tuzilmagan.")
    if not duty_day.is_approved and not perms.can(request.user, "day.view_draft"):
        raise Http404("Bu sutka hali tasdiqlanmagan.")
    return duty_day


@xframe_options_sameorigin  # chop etish sahifasidagi iframe uchun
@perms.role_required("pdf.export")
def day_pdf(request, date):
    from . import pdf

    date = parse_date(date)
    duty_day = _visible_day(request, date)
    return _pdf_response(pdf.render_pdf([duty_day]), pdf.day_filename(date), request.GET.get("inline") == "1")


@perms.role_required("pdf.export")
def day_print(request, date):
    date = parse_date(date)
    _visible_day(request, date)
    return render(request, "naryad/days/print.html", {"date": date, "pdf_url": url_with_inline(date)})


def url_with_inline(date: dt.date) -> str:
    return reverse("day_pdf", args=[date.isoformat()]) + "?inline=1"


@xframe_options_sameorigin
@perms.role_required("pdf.export")
def week_pdf(request, start):
    from . import pdf

    start = parse_date(start)
    week = get_object_or_404(DutyWeek, start_date=start)
    qs = week.days.order_by("date")
    if not perms.can(request.user, "day.view_draft"):
        qs = qs.filter(status=DutyDay.Status.APPROVED)
    duty_days = list(qs)
    if not duty_days:
        raise Http404("Bu haftada hali (tasdiqlangan) sutka yo‘q.")
    return _pdf_response(pdf.render_pdf(duty_days), pdf.week_filename(start), request.GET.get("inline") == "1")
