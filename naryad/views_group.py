"""“Mening guruhim” (19-bosqich): guruh komandiri o'z guruhini FAQAT KO'RADI. Doira — naryad/group_scope.py."""

from __future__ import annotations

import datetime as dt

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from . import i18n
from . import permissions as perms
from .dashboard import current_duty_date, fmt_day
from .group_scope import approved, commander_required, group_summary, scoped_cadet, week_start, week_table
from .models import Absence, Assignment, Penalty
from .services import ServiceError


def _overview_context(request) -> dict:
    query = request.GET.get("q", "").strip()[:50]
    return {"summary": group_summary(request.user, query), "q": query}


@commander_required
def group_overview(request):
    return render(request, "naryad/group/overview.html", _overview_context(request))


@commander_required
def group_status(request):
    """Jonli yangilanish (HTMX, har 60 soniyada): sarlavhadagi sonlar va ro'yxat."""
    return render(request, "naryad/group/_status.html", _overview_context(request))


@commander_required
def group_week(request):
    this_week = week_start(current_duty_date())
    weeks = [week_table(request.user, this_week), week_table(request.user, this_week + dt.timedelta(days=7))]
    for w in weeks:
        w["title"] = f"{fmt_day(w['start'])} → {fmt_day(w['start'] + dt.timedelta(days=7))}"
        w["labels"] = [(d, i18n.weekday(d)[:3]) for d in w["days"]]
    return render(request, "naryad/group/week.html", {"weeks": weeks, "today": current_duty_date()})


@commander_required
def group_cadet(request, pk):
    cadet = scoped_cadet(request.user, pk)  # boshqa guruh — 404
    today = current_duty_date()
    duties = list(approved(Assignment.objects.filter(cadet=cadet)).select_related("duty_day", "post_slot__post").order_by("-duty_day__date")[:30])
    sick = Absence.objects.filter(cadet=cadet, reason_type=Absence.Reason.SICK, start_date__lte=today, end_date__gte=today).first()
    return render(request, "naryad/group/cadet.html", {
        "cadet": cadet, "upcoming": [a for a in reversed(duties) if a.duty_day.date >= today],
        "past": [a for a in duties if a.duty_day.date < today][:15], "sick": sick, "today": today,
    })


# ---------------------------------------------------------------------------
# Zalyot kiritish va o'z guruhi zalyotlari (20-bosqich, CLAUDE.md 68-band)
# ---------------------------------------------------------------------------


@perms.role_required("penalty.group")
@commander_required
def group_penalties(request):
    from .penalties import ledger, with_served

    group = request.commander_group
    qs = with_served(Penalty.objects.filter(cadet__group=group).select_related("cadet"))
    return render(request, "naryad/group/penalties.html", {
        "active": list(qs.filter(status=Penalty.Status.ACTIVE).order_by("order_date", "pk")),
        "finished": list(qs.exclude(status=Penalty.Status.ACTIVE).order_by("-created_at")[:50]),
        "summary": ledger(group=group)["totals"], "group": group,
    })


@perms.role_required("penalty.group")
@commander_required
def group_penalty_add(request):
    """Ikki qadam: forma → tasdiqlash sahifasi (“X (BI-525) ga N ta jazo naryadi kiritiladi”) → saqlash."""
    from . import penalties as penalty_service

    group = request.commander_group
    if request.method == "POST" and request.POST.get("cadet"):
        # Boshqa guruh kursantining id'si — 404 (forma ro'yxatida ham yo'q)
        try:
            scoped_cadet(request.user, int(request.POST["cadet"]))
        except ValueError:
            raise Http404 from None
    form = penalty_service.CommanderPenaltyForm(group, request.POST or None, initial={"order_date": current_duty_date(), "count": 1})
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        if request.POST.get("confirm") != "1":
            return render(request, "naryad/group/penalty_confirm.html", {"form": form, "data": data})
        try:
            penalty = penalty_service.add(data["cadet"], data["reason_type"], data["note"], data["order_date"], data["count"], request.user)
        except penalty_service.DuplicateEntry as exc:
            messages.info(request, str(exc))
            return redirect("group_penalties")
        except ServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, _("%(name)s: zalyot kiritildi — jami %(count)s ta jazo naryadi.") % {
                "name": penalty.cadet.short_name, "count": penalty.count,
            })
            return redirect("group_penalties")
    return render(request, "naryad/group/penalty_form.html", {"form": form, "group": group})
