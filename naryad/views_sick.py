"""Kasallar ro'yxati sahifalari (17-bosqich): ro'yxat, qo'shish, tahrirlash, uzaytirish, “Sog‘ayib qaytdi” — faqat admin."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from . import documents as doc_service
from . import permissions as perms
from . import sick as sick_service
from .absences import can_delete
from .dashboard import current_duty_date
from .models import Absence, SickDocument, StudyGroup


def _warn_conflicts(request, absence: Absence) -> None:
    """Kasallik davri naryad bilan to'qnashsa — admin ogohlantiriladi (tasdiqlangan sutka o'zgarmaydi)."""
    approved, drafts = sick_service.duty_conflicts(absence)
    for day in approved:
        messages.warning(request, sick_service.approved_conflict_text(absence.cadet, day))
    for day in drafts:
        messages.warning(request, sick_service.draft_conflict_text(absence.cadet, day))


def _sick_or_404(pk: int) -> Absence:
    return get_object_or_404(Absence.objects.select_related("cadet__group"), pk=pk, reason_type=sick_service.SICK)


@perms.role_required("sick.manage")
def sick_list(request):
    today = current_duty_date()
    show = request.GET.get("holat", "hozir")
    group = request.GET.get("guruh", "")
    qs = sick_service.sick_records().annotate(doc_count=Count("documents"))
    if show != "hammasi":
        show = "hozir"
        qs = qs.filter(start_date__lte=today, end_date__gte=today)
    if group:
        qs = qs.filter(cadet__group__code=group)
    rows = [{"a": a, "status": sick_service.status(a, today)} for a in qs.order_by("end_date", "cadet__last_name")]
    order = {sick_service.STATUS_ACTIVE: 0, sick_service.STATUS_FUTURE: 1, sick_service.STATUS_DONE: 2}
    rows.sort(key=lambda r: order[r["status"]])
    return render(request, "naryad/sick/list.html", {
        "rows": rows, "today": today, "show": show, "group": group,
        "groups": StudyGroup.objects.order_by("display_order"),
        "titles": sick_service.STATUS_TITLES,
        "active_count": sick_service.sick_records().filter(start_date__lte=today, end_date__gte=today).count(),
    })


@perms.role_required("sick.manage")
def sick_create(request):
    today = current_duty_date()
    form = sick_service.SickForm(request.POST or None, initial={"start_date": today, "end_date": today})
    if request.method == "POST" and form.is_valid():
        absence = sick_service.add(form, request.user)
        messages.success(request, _("%(name)s kasallar ro‘yxatiga kiritildi: %(start)s–%(end)s.") % {
            "name": absence.cadet.short_name, "start": f"{absence.start_date:%d.%m}", "end": f"{absence.end_date:%d.%m}",
        })
        _warn_conflicts(request, absence)
        return redirect("sick_list")
    return render(request, "naryad/sick/form.html", {"form": form})


@perms.role_required("sick.manage")
def sick_edit(request, pk):
    absence = _sick_or_404(pk)
    form = sick_service.SickForm(request.POST or None, instance=absence)
    if request.method == "POST" and form.is_valid():
        sick_service.update(form, request.user)
        messages.success(request, _("O‘zgarishlar saqlandi."))
        _warn_conflicts(request, absence)
        return redirect("sick_edit", pk=absence.pk)
    absence.refresh_from_db()
    return render(request, "naryad/sick/form.html", {
        "form": form, "absence": absence, "extend_form": sick_service.ExtendForm(absence),
        "status": sick_service.status(absence), "titles": sick_service.STATUS_TITLES,
        "recover_blocker": sick_service.recover_blocker(absence), "deletable": can_delete(absence),
        "docs": list(absence.documents.select_related("created_by")), "upload_form": doc_service.UploadForm(),
        "max_docs": doc_service.MAX_DOCUMENTS,
    })


@require_POST
@perms.role_required("sick.manage")
def sick_extend(request, pk):
    absence = _sick_or_404(pk)
    form = sick_service.ExtendForm(absence, request.POST)
    if form.is_valid():
        sick_service.extend(absence, form.cleaned_data["end_date"], request.user)
        messages.success(request, _("%(name)s: kasallik muddati %(day)s gacha uzaytirildi.") % {
            "name": absence.cadet.short_name, "day": f"{absence.end_date:%d.%m.%Y}",
        })
        _warn_conflicts(request, absence)
    else:
        messages.error(request, "; ".join(e for errs in form.errors.values() for e in errs))
    return redirect("sick_edit", pk=absence.pk)


@require_POST
@perms.role_required("sick.manage")
def sick_recover(request, pk):
    absence = _sick_or_404(pk)
    try:
        sick_service.recover(absence, request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("sick_edit", pk=absence.pk)
    messages.success(request, _("%(name)s sog‘ayib qaytdi: muddat %(day)s sutkada tugadi, keyingi sutkadan naryad navbatida.") % {
        "name": absence.cadet.short_name, "day": f"{absence.end_date:%d.%m.%Y}",
    })
    return redirect("sick_list")


@require_POST
@perms.role_required("sick.manage")
def sick_delete(request, pk):
    absence = _sick_or_404(pk)
    try:
        sick_service.delete(absence, request.user)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("sick_edit", pk=absence.pk)
    messages.success(request, _("Yozuv o‘chirildi."))
    return redirect("sick_list")


# ---------------------------------------------------------------------------
# Kasallik hujjatlari (18-bosqich, CLAUDE.md 66-band)
# ---------------------------------------------------------------------------


def _doc_or_404(absence: Absence, doc_id) -> SickDocument:
    return get_object_or_404(SickDocument.objects.select_related("absence__cadet"), pk=doc_id, absence=absence)


def _form_errors(form) -> str:
    return "; ".join(e for errs in form.errors.values() for e in errs)


@require_POST
@perms.role_required("sick.manage")
def doc_upload(request, pk):
    absence = _sick_or_404(pk)
    form = doc_service.UploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, _("Rasm yuklanmadi: %(errors)s") % {"errors": _form_errors(form)})
    else:
        try:
            doc_service.add(absence, form, request.user)
        except doc_service.DocumentError as exc:
            messages.error(request, _("Rasm yuklanmadi: %(errors)s") % {"errors": exc})
        else:
            messages.success(request, _("Hujjat yuklandi."))
    return redirect(reverse("sick_edit", args=[absence.pk]) + "#hujjatlar")


@require_POST
@perms.role_required("sick.manage")
def doc_replace(request, pk, doc_id):
    absence = _sick_or_404(pk)
    doc = _doc_or_404(absence, doc_id)
    form = doc_service.ReplaceForm(request.POST, request.FILES)
    if form.is_valid():
        doc_service.replace(doc, form, request.user)
        messages.success(request, _("Rasm almashtirildi."))
    else:
        messages.error(request, _("Rasm yuklanmadi: %(errors)s") % {"errors": _form_errors(form)})
    return redirect(reverse("sick_edit", args=[absence.pk]) + "#hujjatlar")


@require_POST
@perms.role_required("sick.manage")
def doc_delete(request, pk, doc_id):
    absence = _sick_or_404(pk)
    doc_service.delete(_doc_or_404(absence, doc_id), request.user)
    messages.success(request, _("Hujjat o‘chirildi."))
    return redirect(reverse("sick_edit", args=[absence.pk]) + "#hujjatlar")


def doc_view(request, pk, doc_id):
    """Rasmni beradi: faqat admin yoki o'sha kursant; ommaviy havola yo'q. `?kichik=1` — kichik ko'rinish."""
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path())
    absence = _sick_or_404(pk)
    if not doc_service.can_view(request.user, absence):
        raise PermissionDenied(_("Bu hujjatni ko‘rishga ruxsat yo‘q."))
    small = request.GET.get("kichik") == "1"
    doc = get_object_or_404(SickDocument.objects.with_bytes().only("thumb" if small else "image", "absence_id"),
                            pk=doc_id, absence=absence)
    response = HttpResponse(bytes(doc.thumb if small else doc.image), content_type="image/jpeg")
    response["Content-Disposition"] = 'inline; filename="hujjat.jpg"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    response["X-Robots-Tag"] = "noindex, nofollow"
    return response
