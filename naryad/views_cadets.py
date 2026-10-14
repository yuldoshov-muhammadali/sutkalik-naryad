"""Kursantlar bazasi sahifalari (6-bosqich)."""

from __future__ import annotations

from collections import Counter

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from naryad.engine.names import normalize_apostrophes, short_name as auto_short_name

from . import permissions as perms, stats
from .cadet_import import MAX_FILE_BYTES, ImportFileError, apply_preview, build_preview, preview_from_session, read_xlsx, template_xlsx
from .cadets import (
    CadetForm,
    DeactivateForm,
    ExemptForm,
    UnexemptForm,
    activate,
    approved_count_annotation,
    clear_exempt,
    deactivate,
    has_history,
    open_drafts_with,
    save_cadet,
    set_exempt,
)
from .importers import EXPECTED_COMPOSITION, EXPECTED_TOTAL
from .models import Assignment, Cadet, ChangeLog, DutyDay, Gender, StudyGroup

SESSION_KEY = "cadet_import"


# ---------------------------------------------------------------------------
# Ro'yxat
# ---------------------------------------------------------------------------


def group_summary():
    rows = []
    totals = [0, 0]
    # bitta so'rov: (guruh, jins, faol) bo'yicha sonlar
    counts = Counter(Cadet.objects.values_list("group_id", "gender", "is_active"))
    on_duty = Counter(
        Cadet.objects.filter(gender=Gender.MALE, is_active=True, duty_exempt=False).values_list("group_id", flat=True)
    )
    exempt = Counter(Cadet.objects.filter(is_active=True, duty_exempt=True).values_list("group_id", flat=True))
    for g in StudyGroup.objects.order_by("display_order"):
        boys = counts[(g.pk, Gender.MALE, True)]
        girls = counts[(g.pk, Gender.FEMALE, True)]
        inactive = counts[(g.pk, Gender.MALE, False)] + counts[(g.pk, Gender.FEMALE, False)]
        expected = EXPECTED_COMPOSITION.get(g.code)
        rows.append(
            {"group": g, "boys": boys, "girls": girls, "inactive": inactive, "expected": expected,
             "ok": expected is None or expected == (boys, girls), "on_duty": on_duty[g.pk], "exempt": exempt[g.pk]}
        )
        totals[0] += boys
        totals[1] += girls
    return rows, {
        "boys": totals[0], "girls": totals[1], "expected": EXPECTED_TOTAL, "ok": tuple(totals) == EXPECTED_TOTAL,
        "on_duty": sum(on_duty.values()), "exempt": sum(exempt.values()),
    }


@perms.role_required("cadets.view")
def cadet_list(request):
    group = request.GET.get("guruh", "")
    gender = request.GET.get("jins", "")
    status = request.GET.get("holat", "")
    q = normalize_apostrophes(request.GET.get("q", "").strip())

    qs = Cadet.objects.select_related("group").annotate(duty_count=approved_count_annotation())
    if group:
        qs = qs.filter(group__code=group)
    if gender in (Gender.MALE, Gender.FEMALE):
        qs = qs.filter(gender=gender)
    if status == "faol":
        qs = qs.filter(is_active=True)
    elif status == "faol-emas":
        qs = qs.filter(is_active=False)
    elif status == "naryadga":
        qs = qs.filter(is_active=True, duty_exempt=False)
    elif status == "ozod":
        qs = qs.filter(duty_exempt=True)
    if q:
        qs = qs.filter(last_name__icontains=q)  # familiya bo‘yicha qidiruv
    cadets = list(qs.order_by("group__display_order", "last_name", "first_name"))

    grouped: dict[StudyGroup, list[Cadet]] = {}
    for c in cadets:
        grouped.setdefault(c.group, []).append(c)

    context = {
        "grouped": grouped.items(),
        "count": len(cadets),
        "filters": {"guruh": group, "jins": gender, "holat": status, "q": q},
        "filtered": any([group, gender, status, q]),
    }
    if request.headers.get("HX-Request"):
        return render(request, "naryad/cadets/_results.html", context)
    summary, totals = group_summary()
    context.update({"groups": StudyGroup.objects.order_by("display_order"), "summary": summary, "totals": totals})
    return render(request, "naryad/cadets/list.html", context)


# ---------------------------------------------------------------------------
# Qo'shish / tahrirlash
# ---------------------------------------------------------------------------


@perms.role_required("cadets.manage")
def cadet_create(request):
    form = CadetForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        cadet, _ = save_cadet(form, request.user)
        messages.success(request, f"Kursant qo‘shildi: {cadet.full_name} ({cadet.group.code}).")
        return redirect("cadet_detail", pk=cadet.pk)
    return render(request, "naryad/cadets/form.html", {"form": form, "creating": True})


@perms.role_required("cadets.manage")
def cadet_edit(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    form = CadetForm(request.POST or None, instance=cadet)
    if request.method == "POST" and form.is_valid():
        cadet, changes = save_cadet(form, request.user)
        if changes:
            messages.success(request, "Saqlandi: " + "; ".join(changes) + ".")
        else:
            messages.info(request, "Hech narsa o‘zgarmadi.")
        return redirect("cadet_detail", pk=cadet.pk)
    return render(
        request,
        "naryad/cadets/form.html",
        {"form": form, "creating": False, "cadet": cadet, "has_history": has_history(cadet)},
    )


@perms.role_required("cadets.manage")
def short_name_preview(request):
    last = request.GET.get("last_name", "")
    first = request.GET.get("first_name", "")
    value = auto_short_name(last, first) if last.strip() and first.strip() else ""
    return HttpResponse(value or "—")


# ---------------------------------------------------------------------------
# Faolsizlantirish
# ---------------------------------------------------------------------------


@require_POST
@perms.role_required("cadets.manage")
def cadet_deactivate(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    form = DeactivateForm(request.POST)
    if not cadet.is_active:
        messages.info(request, "Kursant allaqachon faol emas.")
    elif form.is_valid():
        deactivate(cadet, form.reason_text, request.user)
        messages.success(request, f"{cadet.full_name} faolsizlantirildi. Tarixi saqlanadi, generatorga tushmaydi.")
    else:
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        messages.error(request, f"Faolsizlantirilmadi: {errors}")
    return redirect("cadet_detail", pk=cadet.pk)


@require_POST
@perms.role_required("cadets.manage")
def cadet_activate(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    if cadet.is_active:
        messages.info(request, "Kursant allaqachon faol.")
    else:
        activate(cadet, request.user)
        messages.success(request, f"{cadet.full_name} qayta faollashtirildi.")
    return redirect("cadet_detail", pk=cadet.pk)


@require_POST
@perms.role_required("cadets.manage")
def cadet_exempt(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    form = ExemptForm(request.POST)
    if not cadet.is_active:
        messages.error(request, "Faol bo‘lmagan kursantni naryaddan ozod qilib bo‘lmaydi — u baribir naryadga tushmaydi.")
    elif form.is_valid():
        set_exempt(cadet, form.cleaned_data["position"], form.cleaned_data["reason"], request.user)
        messages.success(request, f"{cadet.full_name} naryaddan ozod qilindi ({cadet.duty_position}). Tarixi saqlanadi.")
        for day in open_drafts_with(cadet):
            messages.warning(request, f"{day.date:%d.%m.%Y} qoralamasida turibdi — almashtiring yoki qayta tuzing (tasdiqlab bo‘lmaydi).")
    else:
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        messages.error(request, f"Ozod qilinmadi: {errors}")
    return redirect("cadet_detail", pk=cadet.pk)


@require_POST
@perms.role_required("cadets.manage")
def cadet_unexempt(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    form = UnexemptForm(request.POST)
    if not cadet.duty_exempt:
        messages.info(request, "Kursant naryaddan ozod emas.")
    elif form.is_valid():
        clear_exempt(cadet, form.cleaned_data["reason"], request.user)
        messages.success(
            request,
            f"{cadet.full_name} naryadga qaytarildi. Algoritm uni haftalik va jami hisob bo‘yicha avtomatik oldinga qo‘yadi.",
        )
    else:
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        messages.error(request, f"Qaytarilmadi: {errors}")
    return redirect("cadet_detail", pk=cadet.pk)


# ---------------------------------------------------------------------------
# Kartochka
# ---------------------------------------------------------------------------


@perms.role_required("home.view")
def cadet_detail(request, pk):
    cadet = get_object_or_404(Cadet.objects.select_related("group"), pk=pk)
    is_admin = perms.can(request.user, "history.all")
    if not is_admin:
        own = getattr(request.user, "cadet_id", None)
        if not (perms.can(request.user, "history.own") and own == cadet.pk):
            raise PermissionDenied("Kursant faqat o‘zining kartochkasini ko‘radi.")

    history = list(
        Assignment.objects.filter(cadet=cadet, duty_day__status=DutyDay.Status.APPROVED)
        .select_related("duty_day", "post_slot__post", "group")
        .order_by("-duty_day__date")
    )
    by_post = Counter(a.post_slot.post for a in history)
    by_role = Counter(a.post_slot.get_role_display() for a in history)
    context = {
        "cadet": cadet,
        "history": history,
        "by_post": sorted(by_post.items(), key=lambda kv: kv[0].display_order),
        "by_role": sorted(by_role.items()),
        "is_admin": is_admin,
        "deactivate_form": DeactivateForm() if is_admin else None,
        "exempt_form": ExemptForm(initial={"position": cadet.duty_position}) if is_admin else None,
        "unexempt_form": UnexemptForm() if is_admin else None,
        "log": ChangeLog.objects.filter(cadet=cadet).select_related("user")[:20] if is_admin else [],
        "account": getattr(cadet, "user", None) if is_admin else None,
        "comparison": stats.cadet_comparison(cadet),
    }
    return render(request, "naryad/cadets/detail.html", context)


@perms.role_required("history.own")
def my_card(request):
    if not request.user.cadet_id:
        messages.warning(request, "Akkauntingiz kursantga bog‘lanmagan.")
        return redirect("home")
    return redirect("cadet_detail", pk=request.user.cadet_id)


# ---------------------------------------------------------------------------
# Excel import
# ---------------------------------------------------------------------------


@perms.role_required("cadets.manage")
def cadet_import(request):
    if request.method == "POST" and "file" in request.FILES:
        upload = request.FILES["file"]
        if not upload.name.lower().endswith(".xlsx"):
            messages.error(request, "Faqat .xlsx (Excel) fayl yuklang.")
            return redirect("cadet_import")
        if upload.size > MAX_FILE_BYTES:
            messages.error(request, "Fayl juda katta (2 MB dan oshmasin).")
            return redirect("cadet_import")
        try:
            rows = read_xlsx(upload.read())
        except ImportFileError as exc:
            messages.error(request, str(exc))
            return redirect("cadet_import")
        preview = build_preview(rows)
        request.session[SESSION_KEY] = {"rows": preview.rows, "filename": upload.name, "at": timezone.now().isoformat()}
        return render(request, "naryad/cadets/import.html", {"preview": preview, "filename": upload.name})

    if request.method == "POST" and request.POST.get("action") == "confirm":
        stored = request.session.get(SESSION_KEY)
        if not stored:
            messages.error(request, "Oldindan ko‘rish topilmadi — faylni qayta yuklang.")
            return redirect("cadet_import")
        preview = preview_from_session(stored["rows"])  # baza o'zgargan bo'lishi mumkin — qayta hisoblanadi
        if preview.errors:
            messages.error(request, "Xatoli qatorlar bor — import tasdiqlanmadi. Faylni tuzatib, qayta yuklang.")
            return render(request, "naryad/cadets/import.html", {"preview": preview, "filename": stored["filename"]})
        created, updated = apply_preview(preview, request.user, stored["filename"])
        del request.session[SESSION_KEY]
        messages.success(request, f"Import bajarildi: {created} ta yangi, {updated} ta yangilandi, {len(preview.unchanged)} ta o‘zgarmadi.")
        return redirect("cadet_list")

    if request.method == "POST" and request.POST.get("action") == "cancel":
        request.session.pop(SESSION_KEY, None)
        messages.info(request, "Import bekor qilindi.")
        return redirect("cadet_import")

    return render(request, "naryad/cadets/import.html", {"preview": None})


@perms.role_required("cadets.manage")
def cadet_import_template(request):
    response = HttpResponse(
        template_xlsx(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="kursantlar_shablon.xlsx"'
    return response
