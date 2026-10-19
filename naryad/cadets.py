"""Kursantlar bazasi: forma, qo'shish/tahrirlash, faolsizlantirish va jurnal (6-bosqich)."""

from __future__ import annotations

from django import forms
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone, translation
from django.utils.translation import gettext as _, gettext_lazy as _lazy

from naryad.engine.names import normalize_apostrophes, short_name as auto_short_name

from .models import Assignment, Cadet, ChangeLog, DutyDay, Gender, Penalty, StudyGroup

FIELD_LABELS = {
    "last_name": _lazy("Familiya"),
    "first_name": _lazy("Ism"),
    "patronymic": _lazy("Otasining ismi"),
    "group": _lazy("Guruh"),
    "gender": _lazy("Jinsi"),
    "short_name": _lazy("Qisqa ism"),
}

# Qiymat (birinchi element) bazaga o'zbekcha yoziladi; faqat ko'rinadigan nomi tarjima qilinadi
DEACTIVATION_REASONS = [
    ("Chetlatilgan", _lazy("Chetlatilgan")),
    ("Akademik ta’til", _lazy("Akademik ta’til")),
    ("Boshqa kursga o‘tgan", _lazy("Boshqa kursga o‘tgan")),
    ("Boshqa", _lazy("Boshqa (izohda yozing)")),
]

INPUT_CLASS = (
    "block w-full rounded-lg border border-slate-300 px-3 py-2.5 text-base shadow-sm "
    "focus:border-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-700/30"
)


def has_history(cadet: Cadet) -> bool:
    return cadet.pk is not None and Assignment.objects.filter(cadet=cadet).exists()


def approved_count_annotation():
    return Count("assignments", filter=Q(assignments__duty_day__status=DutyDay.Status.APPROVED))


def duplicate_of(group, last_name: str, first_name: str, patronymic: str, exclude_pk=None) -> Cadet | None:
    qs = Cadet.objects.filter(
        group=group,
        last_name__iexact=last_name,
        first_name__iexact=first_name,
        patronymic__iexact=patronymic,
    )
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    return qs.first()


class CadetForm(forms.ModelForm):
    """Qo'shish va tahrirlash formasi (faqat admin)."""

    confirm_history_change = forms.BooleanField(
        required=False,
        label=_lazy("Tushundim: tarix o‘chmaydi, o‘zgarish faqat keyingi naryadlarga ta’sir qiladi"),
    )

    class Meta:
        model = Cadet
        fields = ["last_name", "first_name", "patronymic", "group", "gender", "short_name"]
        labels = FIELD_LABELS
        help_texts = {
            "short_name": _lazy("Bo‘sh qoldirilsa avtomatik: familiya + ism bosh harfi (Sh, Ch, G‘, O‘ saqlanadi)."),
            "patronymic": _lazy("Masalan: Bahodir o‘g‘li, Oybek qizi, Davronovich."),
        }
        widgets = {"gender": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["group"].queryset = StudyGroup.objects.filter(is_active=True).order_by("display_order")
        self.fields["group"].empty_label = _("— guruhni tanlang —")
        self.fields["patronymic"].required = False
        self.fields["short_name"].required = False
        for name in ("last_name", "first_name", "patronymic", "short_name", "group"):
            self.fields[name].widget.attrs.update({"class": INPUT_CLASS, "autocomplete": "off"})
        self.fields["gender"].choices = Gender.choices
        self._original = {f: getattr(self.instance, f) for f in ("last_name", "first_name", "group_id", "gender")}
        self._auto_before = (
            auto_short_name(self.instance.last_name, self.instance.first_name) if self.instance.pk else ""
        )
        self.history_change_needed = False

    def clean_last_name(self):
        return normalize_apostrophes(self.cleaned_data["last_name"].strip())

    def clean_first_name(self):
        return normalize_apostrophes(self.cleaned_data["first_name"].strip())

    def clean_patronymic(self):
        return normalize_apostrophes((self.cleaned_data.get("patronymic") or "").strip())

    def clean_short_name(self):
        return normalize_apostrophes((self.cleaned_data.get("short_name") or "").strip())

    def clean(self):
        cleaned = super().clean()
        group = cleaned.get("group")
        last, first = cleaned.get("last_name"), cleaned.get("first_name")
        patronymic = cleaned.get("patronymic", "")
        if group and last and first:
            dup = duplicate_of(group, last, first, patronymic, exclude_pk=self.instance.pk)
            if dup:
                raise forms.ValidationError(
                    _("%(group)s guruhida “%(name)s” allaqachon bor — bir xil F.I.Sh. ikki marta kiritilmaydi.")
                    % {"group": group.code, "name": dup.full_name}
                )
            # Qisqa ism: bo'sh yoki avvalgi avtomatik qiymat bo'lsa — qayta hisoblanadi
            if cleaned.get("short_name", "") in ("", self._auto_before):
                cleaned["short_name"] = auto_short_name(last, first)

        if self.instance.pk and has_history(self.instance):
            group_changed = bool(group and group.pk != self._original["group_id"])
            gender_changed = bool(cleaned.get("gender") and cleaned["gender"] != self._original["gender"])
            if group_changed and gender_changed:
                changed = _("guruhi va jinsi")
            elif group_changed:
                changed = _("guruhi")
            elif gender_changed:
                changed = _("jinsi")
            else:
                changed = ""
            if changed and not cleaned.get("confirm_history_change"):
                self.history_change_needed = True
                self.add_error(
                    "confirm_history_change",
                    _(
                        "Bu kursantning naryad tarixi bor, siz %(fields)sni o‘zgartiryapsiz. "
                        "Tarix o‘chmaydi (eski naryadlar o‘sha paytdagi guruh bilan qoladi), o‘zgarish faqat keyingi "
                        "naryadlarga ta’sir qiladi. Davom etish uchun belgini qo‘ying."
                    )
                    % {"fields": changed},
                )
        return cleaned

    def validate_unique(self):
        # Dublikat clean() da o'zbekcha xabar bilan tekshiriladi
        pass


def describe_changes(before: dict, cadet: Cadet) -> list[str]:
    out = []
    for field, label in FIELD_LABELS.items():
        old = before.get(field)
        new = getattr(cadet, "group" if field == "group" else field)
        old_text = str(old) if old is not None else ""
        new_text = str(new) if new is not None else ""
        if field == "gender":
            old_text, new_text = Gender(old).label if old else "", Gender(new).label
        if old_text != new_text:
            out.append(f"{label}: {old_text or '—'} → {new_text or '—'}")
    return out


def snapshot(cadet: Cadet) -> dict:
    return {f: (cadet.group if f == "group" else getattr(cadet, f)) for f in FIELD_LABELS} if cadet.pk else {}


def next_list_number(group: StudyGroup) -> int:
    last = Cadet.objects.filter(group=group).exclude(list_number=None).order_by("-list_number").first()
    return (last.list_number if last else 0) + 1


@transaction.atomic
def save_cadet(form: CadetForm, user) -> tuple[Cadet, list[str]]:
    """Formani saqlaydi va jurnalga yozadi. (kursant, o'zgarishlar ro'yxati) qaytaradi."""
    creating = form.instance.pk is None
    before = {} if creating else snapshot(Cadet.objects.get(pk=form.instance.pk))
    history = not creating and has_history(form.instance)
    cadet = form.save(commit=False)
    cadet.short_name = form.cleaned_data["short_name"]
    if creating or before.get("group") != cadet.group:
        # Yangi kursant yoki boshqa guruhga o'tgan — yangi guruh ro'yxatining oxiriga
        cadet.list_number = next_list_number(cadet.group)
    cadet.save()

    if creating:
        with translation.override("uz"):  # jurnal matni doim o'zbekcha saqlanadi
            details = f"{cadet.full_name}, {cadet.group.code}, {cadet.get_gender_display()}"
        ChangeLog.objects.create(action=ChangeLog.Action.CADET_CREATE, cadet=cadet, user=user, details=details)
        return cadet, []

    changes = describe_changes(before, cadet)  # joriy tilda — xabar uchun
    with translation.override("uz"):  # jurnal matni doim o'zbekcha saqlanadi
        stored = describe_changes(before, cadet)
    if changes:
        details = "; ".join(stored)
        if history and (before["group"] != cadet.group or before["gender"] != cadet.gender):
            details += ". Naryad tarixi bor: tarix o‘chmaydi, o‘zgarish faqat keyingi naryadlarga ta’sir qiladi."
        ChangeLog.objects.create(action=ChangeLog.Action.CADET_UPDATE, cadet=cadet, user=user, details=details)
        linked = getattr(cadet, "user", None)
        if linked is not None and (linked.first_name, linked.last_name) != (cadet.first_name, cadet.last_name):
            linked.first_name, linked.last_name = cadet.first_name, cadet.last_name
            linked.save(update_fields=["first_name", "last_name"])
    return cadet, changes


class DeactivateForm(forms.Form):
    reason = forms.ChoiceField(label=_lazy("Sabab"), choices=DEACTIVATION_REASONS)
    note = forms.CharField(label=_lazy("Izoh"), required=False, max_length=150)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].widget.attrs["class"] = INPUT_CLASS
        self.fields["note"].widget.attrs.update({"class": INPUT_CLASS, "placeholder": _("masalan: buyruq raqami")})

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("reason") == "Boshqa" and not (cleaned.get("note") or "").strip():
            self.add_error("note", _("“Boshqa” sabab uchun izoh majburiy."))
        return cleaned

    @property
    def reason_text(self) -> str:
        # Bazaga yoziladigan sabab: tanlov qiymati (o'zbekcha) + admin izohi — tarjima qilinmaydi
        reason, note = self.cleaned_data["reason"], (self.cleaned_data.get("note") or "").strip()
        if reason == "Boshqa":
            return note
        return f"{reason} ({note})" if note else reason


@transaction.atomic
def deactivate(cadet: Cadet, reason: str, user) -> None:
    """Faolsizlantirish: o'chirilmaydi, tarix va statistika saqlanadi; generatorga tushmaydi."""
    cadet.is_active = False
    cadet.deactivation_reason = reason[:200]
    cadet.deactivated_at = timezone.now()
    cadet.save()
    linked = getattr(cadet, "user", None)
    if linked is not None and linked.is_active:
        linked.is_active = False
        linked.save(update_fields=["is_active"])
    ChangeLog.objects.create(action=ChangeLog.Action.CADET_DEACTIVATE, cadet=cadet, user=user, reason=reason)


@transaction.atomic
def activate(cadet: Cadet, user) -> None:
    old_reason = cadet.deactivation_reason
    cadet.is_active = True
    cadet.save()
    linked = getattr(cadet, "user", None)
    if linked is not None and not linked.is_active:
        linked.is_active = True
        linked.save(update_fields=["is_active"])
    ChangeLog.objects.create(
        action=ChangeLog.Action.CADET_ACTIVATE,
        cadet=cadet,
        user=user,
        details=f"Avvalgi faolsizlantirish sababi: {old_reason}" if old_reason else "",
    )


# ---------------------------------------------------------------------------
# Naryaddan ozod qilish (komandirlar, kurs lavozimlari) — CLAUDE.md 10-bo'lim, 56-band
# ---------------------------------------------------------------------------


class ExemptForm(forms.Form):
    position = forms.CharField(label=_lazy("Lavozimi"), max_length=100)
    reason = forms.CharField(label=_lazy("Sabab"), max_length=200)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["position"].widget.attrs.update({"class": INPUT_CLASS, "placeholder": _("masalan: BI-225 guruh komandiri")})
        self.fields["reason"].widget.attrs.update({"class": INPUT_CLASS, "placeholder": _("masalan: buyruq raqami va sanasi")})

    def clean_position(self):
        return normalize_apostrophes(self.cleaned_data["position"].strip())

    def clean_reason(self):
        return self.cleaned_data["reason"].strip()


class UnexemptForm(forms.Form):
    reason = forms.CharField(label=_lazy("Sabab"), max_length=200)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["reason"].widget.attrs.update({"class": INPUT_CLASS, "placeholder": _("masalan: lavozimdan bo‘shadi (buyruq)")})

    def clean_reason(self):
        return self.cleaned_data["reason"].strip()


def exempt_blocker(cadet: Cadet) -> str | None:
    """Faol zalyoti bor kursantni naryaddan ozod qilib bo'lmaydi (1.6.0 ochiq savoli, CLAUDE.md 62-band)."""
    penalty = Penalty.objects.filter(cadet=cadet, status=Penalty.Status.ACTIVE).first()
    if penalty is not None:
        return _(
            "%(name)s faol zalyotchik (%(count)s ta jazo naryadi) — avval zalyot bajarilishi yoki bekor qilinishi kerak, "
            "keyin “naryadga chiqmaydi” deb belgilanadi."
        ) % {"name": cadet.short_name, "count": penalty.count}
    return None


@transaction.atomic
def set_exempt(cadet: Cadet, position: str, reason: str, user) -> None:
    """Naryaddan ozod: kursant faol qoladi (akkaunti ishlaydi), faqat naryadga qo'yilmaydi."""
    blocker = exempt_blocker(cadet)
    if blocker:
        raise ValueError(blocker)
    old = cadet.duty_position if cadet.duty_exempt else ""
    cadet.duty_exempt = True
    cadet.duty_position = position[:100]
    cadet.save(update_fields=["duty_exempt", "duty_position", "updated_at"])
    details = f"Lavozimi: {cadet.duty_position}" + (f" (avval: {old})" if old and old != cadet.duty_position else "")
    ChangeLog.objects.create(action=ChangeLog.Action.CADET_EXEMPT, cadet=cadet, user=user, reason=reason, details=details)


@transaction.atomic
def clear_exempt(cadet: Cadet, reason: str, user) -> None:
    """Lavozimdan bo'shadi — qayta naryadga qo'shiladi (algoritm uni hisob bo'yicha o'zi oldinga qo'yadi)."""
    old = cadet.duty_position
    cadet.duty_exempt = False
    cadet.duty_position = ""
    cadet.save(update_fields=["duty_exempt", "duty_position", "updated_at"])
    ChangeLog.objects.create(
        action=ChangeLog.Action.CADET_UNEXEMPT, cadet=cadet, user=user, reason=reason, details=f"Avvalgi lavozimi: {old}"
    )


def open_drafts_with(cadet: Cadet) -> list[DutyDay]:
    return list(DutyDay.objects.filter(status=DutyDay.Status.DRAFT, assignments__cadet=cadet).order_by("date"))
