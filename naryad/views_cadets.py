"""Kursantlar bazasi sahifalari (6-bosqich)."""

from __future__ import annotations

from collections import Counter

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext
from django.views.decorators.http import require_POST

from naryad.engine.names import normalize_apostrophes
from naryad.engine.names import short_name as auto_short_name

from . import penalties as penalty_service
from . import permissions as perms
from . import stats
from .cadet_import import (
    MAX_FILE_BYTES,
    ImportFileError,
    apply_preview,
    build_preview,
    preview_from_session,
    read_xlsx,
    template_xlsx,
)
from .cadets import (
    CadetForm,
    DeactivateForm,
    ExemptForm,
    UnexemptForm,
    activate,
    approved_count_annotation,
    clear_exempt,
    deactivate,
    exempt_blocker,
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
        cadet, _changes = save_cadet(form, request.user)
        messages.success(
            request, _("Kursant qo‘shildi: %(name)s (%(group)s).") % {"name": cadet.full_name, "group": cadet.group.code}
        )
        return redirect("cadet_detail", pk=cadet.pk)
    return render(request, "naryad/cadets/form.html", {"form": form, "creating": True})


@perms.role_required("cadets.manage")
def cadet_edit(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    form = CadetForm(request.POST or None, instance=cadet)
    if request.method == "POST" and form.is_valid():
        cadet, changes = save_cadet(form, request.user)
        if changes:
            messages.success(request, _("Saqlandi: %(changes)s.") % {"changes": "; ".join(changes)})
        else:
            messages.info(request, _("Hech narsa o‘zgarmadi."))
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
        messages.info(request, _("Kursant allaqachon faol emas."))
    elif form.is_valid():
        deactivate(cadet, form.reason_text, request.user)
        messages.success(
            request, _("%(name)s faolsizlantirildi. Tarixi saqlanadi, generatorga tushmaydi.") % {"name": cadet.full_name}
        )
    else:
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        messages.error(request, _("Faolsizlantirilmadi: %(errors)s") % {"errors": errors})
    return redirect("cadet_detail", pk=cadet.pk)


@require_POST
@perms.role_required("cadets.manage")
def cadet_activate(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    if cadet.is_active:
        messages.info(request, _("Kursant allaqachon faol."))
    else:
        activate(cadet, request.user)
        messages.success(request, _("%(name)s qayta faollashtirildi.") % {"name": cadet.full_name})
    return redirect("cadet_detail", pk=cadet.pk)


@require_POST
@perms.role_required("cadets.manage")
def cadet_exempt(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    form = ExemptForm(request.POST)
    if not cadet.is_active:
        messages.error(request, _("Faol bo‘lmagan kursantni naryaddan ozod qilib bo‘lmaydi — u baribir naryadga tushmaydi."))
    elif exempt_blocker(cadet):
        messages.error(request, exempt_blocker(cadet))
    elif form.is_valid():
        set_exempt(cadet, form.cleaned_data["position"], form.cleaned_data["reason"], request.user)
        messages.success(
            request,
            _("%(name)s naryaddan ozod qilindi (%(position)s). Tarixi saqlanadi.")
            % {"name": cadet.full_name, "position": cadet.duty_position},
        )
        for day in open_drafts_with(cadet):
            messages.warning(
                request,
                _("%(date)s qoralamasida turibdi — almashtiring yoki qayta tuzing (tasdiqlab bo‘lmaydi).")
                % {"date": f"{day.date:%d.%m.%Y}"},
            )
    else:
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        messages.error(request, _("Ozod qilinmadi: %(errors)s") % {"errors": errors})
    return redirect("cadet_detail", pk=cadet.pk)


@require_POST
@perms.role_required("cadets.manage")
def cadet_unexempt(request, pk):
    cadet = get_object_or_404(Cadet, pk=pk)
    form = UnexemptForm(request.POST)
    if not cadet.duty_exempt:
        messages.info(request, _("Kursant naryaddan ozod emas."))
    elif form.is_valid():
        clear_exempt(cadet, form.cleaned_data["reason"], request.user)
        messages.success(
            request,
            _("%(name)s naryadga qaytarildi. Algoritm uni haftalik va jami hisob bo‘yicha avtomatik oldinga qo‘yadi.")
            % {"name": cadet.full_name},
        )
    else:
        errors = "; ".join(e for errs in form.errors.values() for e in errs)
        messages.error(request, _("Qaytarilmadi: %(errors)s") % {"errors": errors})
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
            raise PermissionDenied(_("Kursant faqat o‘zining kartochkasini ko‘radi."))

    history = list(
        Assignment.objects.filter(cadet=cadet, duty_day__status=DutyDay.Status.APPROVED)
        .select_related("duty_day", "post_slot__post", "group")
        .order_by("-duty_day__date")
    )
    normal = [a for a in history if a.kind == Assignment.Kind.NORMAL]  # jazo naryadlari adolat hisobiga kirmaydi
    by_post = Counter(a.post_slot.post for a in normal)
    by_role = Counter(a.post_slot.get_role_display() for a in normal)
    context = {
        "cadet": cadet,
        "history": history,
        "normal_total": len(normal),
        "penalty_total": len(history) - len(normal),
        "penalties": list(
            penalty_service.with_served(cadet.penalties.select_related("created_by")).order_by("-created_at")
        ) if is_admin else [],
        "by_post": sorted(by_post.items(), key=lambda kv: kv[0].display_order),
        "by_role": sorted(by_role.items()),
        "is_admin": is_admin,
        "deactivate_form": DeactivateForm() if is_admin else None,
        "exempt_form": ExemptForm(initial={"position": cadet.duty_position}) if is_admin else None,
        "exempt_blocker": exempt_blocker(cadet) if is_admin and not cadet.duty_exempt else None,
        "unexempt_form": UnexemptForm() if is_admin else None,
        "log": ChangeLog.objects.filter(cadet=cadet).select_related("user")[:20] if is_admin else [],
        "account": getattr(cadet, "user", None) if is_admin else None,
        "comparison": stats.cadet_comparison(cadet),
    }
    return render(request, "naryad/cadets/detail.html", context)


@perms.role_required("history.own")
def my_card(request):
    if not request.user.cadet_id:
        messages.warning(request, _("Akkauntingiz kursantga bog‘lanmagan."))
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
            messages.error(request, _("Faqat .xlsx (Excel) fayl yuklang."))
            return redirect("cadet_import")
        if upload.size > MAX_FILE_BYTES:
            messages.error(request, _("Fayl juda katta (2 MB dan oshmasin)."))
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
            messages.error(request, _("Oldindan ko‘rish topilmadi — faylni qayta yuklang."))
            return redirect("cadet_import")
        preview = preview_from_session(stored["rows"])  # baza o'zgargan bo'lishi mumkin — qayta hisoblanadi
        if preview.errors:
            messages.error(request, _("Xatoli qatorlar bor — import tasdiqlanmadi. Faylni tuzatib, qayta yuklang."))
            return render(request, "naryad/cadets/import.html", {"preview": preview, "filename": stored["filename"]})
        created, updated = apply_preview(preview, request.user, stored["filename"])
        del request.session[SESSION_KEY]
        messages.success(
            request,
            _("Import bajarildi: %(created)s, %(updated)s, %(unchanged)s.")
            % {
                "created": ngettext("%(n)s ta yangi", "%(n)s ta yangi", created) % {"n": created},
                "updated": ngettext("%(n)s ta yangilandi", "%(n)s ta yangilandi", updated) % {"n": updated},
                "unchanged": ngettext("%(n)s ta o‘zgarmadi", "%(n)s ta o‘zgarmadi", len(preview.unchanged))
                % {"n": len(preview.unchanged)},
            },
        )
        return redirect("cadet_list")

    if request.method == "POST" and request.POST.get("action") == "cancel":
        request.session.pop(SESSION_KEY, None)
        messages.info(request, _("Import bekor qilindi."))
        return redirect("cadet_import")

    return render(request, "naryad/cadets/import.html", {"preview": None})


@perms.role_required("cadets.manage")
def cadet_import_template(request):
    response = HttpResponse(
        template_xlsx(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="kursantlar_shablon.xlsx"'
    return response
