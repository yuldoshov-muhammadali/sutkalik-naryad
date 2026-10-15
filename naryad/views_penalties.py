"""Zalyotchiklar sahifasi (15-bosqich): faol va yakunlangan zalyotlar, kiritish, bekor qilish — faqat admin."""

from __future__ import annotations

from collections import defaultdict

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from . import penalties as penalty_service
from . import permissions as perms
from .dashboard import current_duty_date
from .models import Assignment, DutyDay, Penalty
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
        except ServiceError as exc:
            form.add_error(None, str(exc))
        else:
            messages.success(request, _("%(name)s: zalyot kiritildi — jami %(count)s ta jazo naryadi.") % {
                "name": penalty.cadet.short_name, "count": penalty.count,
            })
            return redirect("penalty_list")
    qs = penalty_service.with_served(Penalty.objects.select_related("cadet__group", "created_by"))
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
