"""Sababli holatlar (kasal / ta'til / sababli / boshqa) — 7-bosqich.

Sanalar sutka boshlanish sanalari, ikkala chegara ham ichida. Allaqachon boshlangan
(tarixi bor) yozuv o'chirilmaydi — faqat tugash sanasi o'zgartiriladi.
"""

from __future__ import annotations

import datetime as dt

from django import forms
from django.db import transaction
from django.utils import translation
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from .cadets import INPUT_CLASS
from .dashboard import current_duty_date
from .models import Absence, Cadet, ChangeLog


def overlapping(cadet_id: int, start: dt.date, end: dt.date, exclude_pk=None):
    qs = Absence.objects.filter(cadet_id=cadet_id, start_date__lte=end, end_date__gte=start)
    return qs.exclude(pk=exclude_pk) if exclude_pk else qs


def can_delete(absence: Absence, today: dt.date | None = None) -> bool:
    """Hali boshlanmagan yozuvni o'chirish mumkin; boshlangani (tarixi bor) — faqat tugash sanasini o'zgartirish."""
    return absence.start_date > (today or current_duty_date())


class AbsenceForm(forms.ModelForm):
    class Meta:
        model = Absence
        fields = ["cadet", "reason_type", "start_date", "end_date", "note"]
        labels = {
            "cadet": _lazy("Kursant"),
            "reason_type": _lazy("Sabab"),
            "start_date": _lazy("Birinchi sutka"),
            "end_date": _lazy("Oxirgi sutka (ichida)"),
            "note": _lazy("Izoh"),
        }
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "end_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cadet"].queryset = Cadet.objects.filter(is_active=True).select_related("group").order_by(
            "group__display_order", "last_name"
        )
        self.fields["cadet"].label_from_instance = lambda c: f"{c.group.code} · {c.full_name}"
        self.fields["cadet"].empty_label = _("— kursantni tanlang —")
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", INPUT_CLASS)

    def clean(self):
        cleaned = super().clean()
        cadet, start, end = cleaned.get("cadet"), cleaned.get("start_date"), cleaned.get("end_date")
        if cadet and start and end:
            if end < start:
                self.add_error("end_date", _("Oxirgi sutka birinchisidan oldin bo‘lishi mumkin emas."))
            else:
                other = overlapping(cadet.pk, start, end).first()
                if other:
                    raise forms.ValidationError(
                        _(
                            "%(name)s uchun bu sanalarga allaqachon yozuv bor: "
                            "%(reason)s %(start)s–%(end)s. "
                            "O‘sha yozuvning tugash sanasini o‘zgartiring."
                        ) % {
                            "name": cadet.short_name, "reason": other.get_reason_type_display(),
                            "start": f"{other.start_date:%d.%m}", "end": f"{other.end_date:%d.%m}",
                        }
                    )
        return cleaned


class EndDateForm(forms.Form):
    end_date = forms.DateField(label=_lazy("Yangi tugash sanasi"), widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, absence: Absence, *args, **kwargs):
        self.absence = absence
        super().__init__(*args, **kwargs)
        self.fields["end_date"].widget.attrs["class"] = INPUT_CLASS

    def clean_end_date(self):
        end = self.cleaned_data["end_date"]
        if end < self.absence.start_date:
            raise forms.ValidationError(_("Tugash sanasi boshlanish sanasidan oldin bo‘lishi mumkin emas."))
        if overlapping(self.absence.cadet_id, self.absence.start_date, end, exclude_pk=self.absence.pk).exists():
            raise forms.ValidationError(_("Bu sanalarda shu kursantning boshqa yozuvi bor."))
        return end


def _summary(a: Absence) -> str:
    """ChangeLog.details uchun — saqlanadigan matn, doim o'zbekcha."""
    with translation.override("uz"):
        return f"{a.get_reason_type_display()}: {a.start_date:%d.%m.%Y}–{a.end_date:%d.%m.%Y}" + (f" ({a.note})" if a.note else "")


@transaction.atomic
def add(form: AbsenceForm, user) -> Absence:
    absence = form.save(commit=False)
    absence.created_by = user
    absence.full_clean()
    absence.save()
    ChangeLog.objects.create(action=ChangeLog.Action.ABSENCE_ADD, cadet=absence.cadet, user=user, details=_summary(absence))
    return absence


@transaction.atomic
def change_end(absence: Absence, end: dt.date, user) -> None:
    old = absence.end_date
    absence.end_date = end
    absence.save(update_fields=["end_date"])
    with translation.override("uz"):  # ChangeLog.details — saqlanadigan matn, doim o'zbekcha
        details = f"{absence.get_reason_type_display()} {absence.start_date:%d.%m.%Y}: tugash {old:%d.%m.%Y} → {end:%d.%m.%Y}"
    ChangeLog.objects.create(action=ChangeLog.Action.ABSENCE_CHANGE, cadet=absence.cadet, user=user, details=details)


@transaction.atomic
def delete(absence: Absence, user) -> None:
    ChangeLog.objects.create(action=ChangeLog.Action.ABSENCE_DELETE, cadet=absence.cadet, user=user, details=_summary(absence))
    absence.delete()
