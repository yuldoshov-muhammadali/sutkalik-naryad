"""Zalyotchiklar sahifasi (15-bosqich): faol va yakunlangan zalyotlar, kiritish, bekor qilish — faqat admin."""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from . import penalties as penalty_service
from . import permissions as perms
from .dashboard import current_duty_date
from .models import Assignment, DutyDay, Penalty, StudyGroup
from .services import ServiceError


@perms.role_required("penalty.manage")
def penalty_list(request):
    form = penalty_service.PenaltyForm(request.POST or None, initial={"order_date": current_duty_date(), "count": 1})
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            penalty = penalty_service.add(
                data["cadet"], data["reason_type"], data["note"], data["order_date"], data["count"], request.user
            )
        except penalty_service.DuplicateEntry as exc:
            messages.info(request, str(exc))
            return redirect("penalty_list")
        except ServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, _("%(name)s: zalyot kiritildi — jami %(count)s ta jazo naryadi.") % {
                "name": penalty.cadet.short_name, "count": penalty.count,
            })
            return redirect("penalty_list")
    qs = penalty_service.with_served(Penalty.objects.select_related("cadet__group", "created_by", "reviewed_by"))
    active = list(qs.filter(status=Penalty.Status.ACTIVE).order_by("order_date", "pk"))
    finished = list(qs.exclude(status=Penalty.Status.ACTIVE).order_by("-finished_at", "-pk")[:50])
    # Har zalyotning jazo naryadlari (tasdiqlangan — o'tilgan, qoralama — rejada)
    served_days = defaultdict(list)
    for a in (
        Assignment.objects.filter(penalty__in=active + finished)
        .select_related("duty_day", "post_slot__post")
        .order_by("duty_day__date")
    ):
        served_days[a.penalty_id].append(a)
    for p in active + finished:
        p.duty_list = served_days.get(p.pk, [])
    return render(request, "naryad/penalties/list.html", {
        "form": form, "active": active, "finished": finished, "cancel_form": penalty_service.CancelForm(),
        "approved": DutyDay.Status.APPROVED,
    })


@require_POST
@perms.role_required("penalty.manage")
def penalty_cancel(request, pk):
    penalty = get_object_or_404(Penalty.objects.select_related("cadet"), pk=pk)
    form = penalty_service.CancelForm(request.POST)
    if not form.is_valid():
        messages.error(request, _("Bekor qilish sababi majburiy."))
        return redirect("penalty_list")
    try:
        penalty_service.cancel(penalty, form.cleaned_data["reason"], request.user)
    except ServiceError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, _("%(name)s: zalyot bekor qilindi.") % {"name": penalty.cadet.short_name})
    return redirect("penalty_list")


# ---------------------------------------------------------------------------
# 20-bosqich: tahrir, “Ko'rib chiqildi”, hisob
# ---------------------------------------------------------------------------


@perms.role_required("penalty.manage")
def penalty_edit(request, pk):
    penalty = get_object_or_404(penalty_service.with_served(Penalty.objects.select_related("cadet__group", "created_by")), pk=pk)
    initial = {"reason_type": penalty.reason_type, "order_date": penalty.order_date, "count": penalty.count, "note": penalty.note}
    form = penalty_service.EditForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        try:
            penalty_service.edit(penalty, data["reason_type"], data["note"], data["order_date"], data["count"], request.user)
        except ServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, _("%(name)s: zalyot o‘zgartirildi.") % {"name": penalty.cadet.short_name})
            return redirect("penalty_list")
    entries = penalty.entries.select_related("created_by")
    return render(request, "naryad/penalties/edit.html", {"penalty": penalty, "form": form, "entries": entries,
                                                          "cancel_form": penalty_service.CancelForm()})


@require_POST
@perms.role_required("penalty.manage")
def penalty_review(request, pk):
    penalty_service.review(Penalty.objects.filter(pk=pk), request.user)
    return redirect(request.POST.get("next") if url_has_allowed_host_and_scheme(request.POST.get("next"), None) else "penalty_list")


@require_POST
@perms.role_required("penalty.manage")
def penalty_review_all(request):
    n = penalty_service.review(penalty_service.unreviewed(), request.user)
    messages.success(request, _("Ko‘rib chiqildi: %(n)s ta zalyot.") % {"n": n})
    return redirect(request.POST.get("next") if url_has_allowed_host_and_scheme(request.POST.get("next"), None) else "penalty_list")


def _ledger_params(request):
    def parse(name):
        try:
            return dt.date.fromisoformat(request.GET.get(name, ""))
        except ValueError:
            return None

    group = StudyGroup.objects.filter(code=request.GET.get("guruh", "")).first()
    return parse("dan"), parse("gacha"), group


@perms.role_required("penalty.manage")
def penalty_ledger(request):
    date_from, date_to, group = _ledger_params(request)
    data = penalty_service.ledger(date_from, date_to, group)
    for row in data["users"]:
        row.label = penalty_service.user_label(row.key)
    return render(request, "naryad/penalties/ledger.html", {
        **data, "date_from": date_from, "date_to": date_to, "group": group,
        "groups_all": StudyGroup.objects.order_by("display_order"), "query": request.GET.urlencode(),
    })


@perms.role_required("penalty.manage")
def penalty_ledger_excel(request):
    from django.http import HttpResponse

    date_from, date_to, group = _ledger_params(request)
    content = penalty_service.ledger_xlsx(penalty_service.ledger(date_from, date_to, group), date_from, date_to)
    response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="zalyot_hisobi_{current_duty_date():%Y-%m-%d}.xlsx"'
    return response
