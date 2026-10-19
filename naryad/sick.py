"""Kasallar ro'yxati (17-bosqich, CLAUDE.md 64-band).

Alohida jadval yo'q: kasallik — `Absence` (`reason_type = "kasal"`) + `illness` (qisqa tavsif).
Shuning uchun generator, almashtirish oynasi va “Sababli holatlar” sahifasi uni avtomatik hisobga oladi.
Sanalar — sutka boshlanish sanalari, ikkala chegara ham ichida. Tavsifni faqat admin ko'radi.
"""

from __future__ import annotations

import datetime as dt

from django import forms
from django.db import transaction
from django.utils import translation
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from .absences import can_delete, overlapping
from .cadets import INPUT_CLASS
from .dashboard import current_duty_date
from .models import Absence, Assignment, Cadet, ChangeLog, DutyDay

SICK = Absence.Reason.SICK
DATE_WIDGET = {"type": "date"}

STATUS_ACTIVE, STATUS_DONE, STATUS_FUTURE = "active", "done", "future"
STATUS_TITLES = {
    STATUS_ACTIVE: _lazy("davom etmoqda"),
    STATUS_DONE: _lazy("tugagan"),
    STATUS_FUTURE: _lazy("kelajakda"),
}


def sick_records():
    return Absence.objects.filter(reason_type=SICK).select_related("cadet__group", "created_by")


def status(absence: Absence, today: dt.date | None = None) -> str:
    today = today or current_duty_date()
    if absence.start_date > today:
        return STATUS_FUTURE
    return STATUS_DONE if absence.end_date < today else STATUS_ACTIVE


def current_sickness(cadet: Cadet, today: dt.date | None = None) -> Absence | None:
    """Kursant hozir kasallar ro'yxatidami (bugungi sutka muddat ichida)."""
    today = today or current_duty_date()
    return Absence.objects.filter(cadet=cadet, reason_type=SICK, start_date__lte=today, end_date__gte=today).first()


def overlap_error(cadet: Cadet, start: dt.date, end: dt.date, exclude_pk=None) -> str | None:
    other = overlapping(cadet.pk, start, end, exclude_pk=exclude_pk).first()
    if other is None:
        return None
    return _(
        "%(name)s uchun bu sanalarga allaqachon yozuv bor: %(reason)s %(start)s–%(end)s. "
        "O‘sha yozuvning tugash sanasini o‘zgartiring."
    ) % {
        "name": cadet.short_name, "reason": other.get_reason_type_display(),
        "start": f"{other.start_date:%d.%m}", "end": f"{other.end_date:%d.%m}",
    }


class SickForm(forms.ModelForm):
    """Qo'shish va tahrirlash. Tahrirda kursant o'zgarmaydi; boshlangan yozuvda boshlanish sanasi ham (36-band)."""

    class Meta:
        model = Absence
        fields = ["cadet", "illness", "start_date", "end_date"]
        labels = {
            "cadet": _lazy("Kursant"),
            "illness": _lazy("Kasallik (qisqa tavsif)"),
            "start_date": _lazy("Qachondan beri kasal"),
            "end_date": _lazy("Muddati (oxirgi sutka, ichida)"),
        }
        help_texts = {"end_date": _lazy("Aniq bo‘lmasa — taxminiy sana; keyin “Muddatni uzaytirish”.")}
        widgets = {
            "start_date": forms.DateInput(attrs=DATE_WIDGET, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs=DATE_WIDGET, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        editing = self.instance.pk is not None
        self.fields["illness"].required = True
        self.fields["illness"].widget.attrs["placeholder"] = _("masalan: gripp, harorat")
        if editing:
            del self.fields["cadet"]
            if not can_delete(self.instance):  # boshlangan — boshlanish sanasi o'zgarmaydi
                self.fields["start_date"].disabled = True
        else:
            self.fields["cadet"].queryset = Cadet.objects.filter(is_active=True).select_related("group").order_by(
                "group__display_order", "last_name", "first_name"
            )
            self.fields["cadet"].label_from_instance = lambda c: f"{c.full_name} · {c.group.code}"
            self.fields["cadet"].empty_label = _("— kursantni tanlang —")
            self.fields["cadet"].widget.attrs["size"] = "7"  # ro'yxat ko'rinib turadi — qidiruv natijasi darhol ko'rinadi
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", INPUT_CLASS)

    def clean_illness(self):
        return self.cleaned_data["illness"].strip()

    def clean(self):
        cleaned = super().clean()
        cadet = cleaned.get("cadet") if "cadet" in self.fields else self.instance.cadet
        start, end = cleaned.get("start_date"), cleaned.get("end_date")
        if cadet and start and end:
            if end < start:
                self.add_error("end_date", _("Oxirgi sutka birinchisidan oldin bo‘lishi mumkin emas."))
            else:
                error = overlap_error(cadet, start, end, exclude_pk=self.instance.pk)
                if error:
                    raise forms.ValidationError(error)
        return cleaned


class ExtendForm(forms.Form):
    end_date = forms.DateField(label=_lazy("Yangi muddat (oxirgi sutka)"), widget=forms.DateInput(attrs=DATE_WIDGET))

    def __init__(self, absence: Absence, *args, **kwargs):
        self.absence = absence
        super().__init__(*args, **kwargs)
        self.fields["end_date"].widget.attrs.update({"class": INPUT_CLASS, "min": f"{absence.end_date + dt.timedelta(days=1):%Y-%m-%d}"})

    def clean_end_date(self):
        end = self.cleaned_data["end_date"]
        if end <= self.absence.end_date:
            raise forms.ValidationError(_("Yangi muddat hozirgisidan (%(day)s) keyin bo‘lishi kerak.") % {
                "day": f"{self.absence.end_date:%d.%m.%Y}",
            })
        error = overlap_error(self.absence.cadet, self.absence.start_date, end, exclude_pk=self.absence.pk)
        if error:
            raise forms.ValidationError(error)
        return end


def _summary(a: Absence) -> str:
    """ChangeLog.details — saqlanadigan matn, doim o'zbekcha."""
    return f"{a.start_date:%d.%m.%Y}–{a.end_date:%d.%m.%Y}" + (f" ({a.illness})" if a.illness else "")


def _log(action: str, absence: Absence, user, details: str) -> None:
    with translation.override("uz"):
        ChangeLog.objects.create(action=action, cadet=absence.cadet, user=user, details=details)


@transaction.atomic
def add(form: SickForm, user) -> Absence:
    absence = form.save(commit=False)
    absence.reason_type = SICK
    absence.created_by = user
    absence.full_clean()
    absence.save()
    _log(ChangeLog.Action.SICK_ADD, absence, user, _summary(absence))
    return absence


@transaction.atomic
def update(form: SickForm, user) -> Absence:
    old = Absence.objects.get(pk=form.instance.pk)
    absence = form.save()
    _log(ChangeLog.Action.SICK_EDIT, absence, user, f"{_summary(old)} → {_summary(absence)}")
    return absence


@transaction.atomic
def extend(absence: Absence, end: dt.date, user) -> None:
    old = absence.end_date
    absence.end_date = end
    absence.save(update_fields=["end_date"])
    _log(ChangeLog.Action.SICK_EXTEND, absence, user, f"{absence.start_date:%d.%m.%Y}: muddat {old:%d.%m.%Y} → {end:%d.%m.%Y}")


def recover_blocker(absence: Absence, today: dt.date | None = None) -> str | None:
    today = today or current_duty_date()
    if absence.start_date > today:
        return _("Kasallik hali boshlanmagan — yozuvni o‘chiring.")
    if absence.end_date <= today:
        return _("Kasallik muddati allaqachon tugagan.")
    return None


@transaction.atomic
def recover(absence: Absence, user, today: dt.date | None = None) -> None:
    """“Sog‘ayib qaytdi”: tugash sanasi bugungi sutka bo'ladi — ertangi sutkadan oddiy navbatga qaytadi."""
    today = today or current_duty_date()
    blocker = recover_blocker(absence, today)
    if blocker:
        raise ValueError(blocker)
    old = absence.end_date
    absence.end_date = today
    absence.save(update_fields=["end_date"])
    _log(ChangeLog.Action.SICK_RECOVER, absence, user, f"{absence.start_date:%d.%m.%Y}: muddat {old:%d.%m.%Y} → {today:%d.%m.%Y}")


@transaction.atomic
def delete(absence: Absence, user) -> None:
    if not can_delete(absence):
        raise ValueError(_("Boshlangan (tarixi bor) yozuv o‘chirilmaydi — muddatini o‘zgartiring."))
    docs = absence.documents.count()  # hujjat rasmlari ham bazadan o'chadi (CASCADE); jurnalda faqat soni
    _log(ChangeLog.Action.SICK_DELETE, absence, user, _summary(absence) + (f"; {docs} ta hujjat rasmi ham o‘chirildi" if docs else ""))
    absence.delete()


def duty_conflicts(absence: Absence) -> tuple[list[dt.date], list[dt.date]]:
    """Kasallik davriga to'g'ri kelgan naryadlari: (tasdiqlangan sutkalar, qoralamalar). Tasdiqlangani o'zgarmaydi."""
    qs = Assignment.objects.filter(
        cadet=absence.cadet, duty_day__date__gte=absence.start_date, duty_day__date__lte=absence.end_date
    ).values_list("duty_day__date", "duty_day__status").order_by("duty_day__date")
    approved = [d for d, st in qs if st == DutyDay.Status.APPROVED]
    drafts = [d for d, st in qs if st != DutyDay.Status.APPROVED]
    return approved, drafts


def approved_conflict_text(cadet: Cadet, day: dt.date) -> str:
    return _("%(name)s %(day)s sutkada naryadda, u tasdiqlangan. Almashtirish uchun avval tasdiqni bekor qiling.") % {
        "name": cadet.short_name, "day": f"{day:%d.%m.%Y}",
    }


def draft_conflict_text(cadet: Cadet, day: dt.date) -> str:
    return _("%(name)s %(day)s qoralamasida turibdi — sutka sahifasida “Almashtirish” bilan boshqa kursant qo‘ying.") % {
        "name": cadet.short_name, "day": f"{day:%d.%m.%Y}",
    }
