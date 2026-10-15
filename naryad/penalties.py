"""Zalyotchiklar — navbatdan tashqari jazo naryadi (15-bosqich, CLAUDE.md 10-bo'lim, 61-band).

- Admin zalyot kiritadi (kursant, sabab turi, izoh, tanbeh sanasi, 1–10 ta naryad); bir kursantda bitta faol
  zalyot — yangisi qo'shilsa soni mavjudiga qo'shiladi (jurnalda alohida yozuv).
- Faqat o'g'il, faol va naryaddan ozod bo'lmagan kursant zalyotchik bo'ladi.
- Jazo naryadi “o'tildi” deb faqat sutka TASDIQLANGANDA hisoblanadi; tasdiq bekor qilinsa hisob qaytadi.
  Soni tugagach zalyot avtomatik “bajarildi”.
- Algoritmga faol zalyotchiklar `engine.Offender` sifatida beriladi (naryad/engine/allocator.py: place_offenders).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable

from django import forms
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

from naryad.engine import models as em

from .cadets import INPUT_CLASS
from .models import Assignment, Cadet, ChangeLog, DutyDay, Gender, Penalty
from .services import ServiceError


def offender_error(cadet: Cadet) -> str | None:
    """Standart qoidalar: faqat o'g'il, faol, naryaddan ozod bo'lmagan kursant zalyotchik bo'ladi."""
    if cadet.gender != Gender.MALE:
        return _("Zalyotchik faqat o‘g‘il kursant bo‘ladi (jazo o‘rinlari — 1-NO‘J va 1-Yotoqxona o‘g‘illar joyi).")
    if not cadet.is_active:
        return _("%(name)s faol emas — zalyotchik qilib bo‘lmaydi.") % {"name": cadet.short_name}
    if cadet.duty_exempt:
        return _("%(name)s naryaddan ozod (%(position)s) — avval ozodlikni olib tashlang.") % {
            "name": cadet.short_name, "position": cadet.duty_position,
        }
    return None


def with_served(qs):
    """`served_count` — tasdiqlangan sutkalardagi jazo naryadlari soni (N+1 bo'lmasin)."""
    return qs.annotate(
        served_count=Count("assignments", filter=Q(assignments__duty_day__status=DutyDay.Status.APPROVED))
    )


def active_penalty(cadet: Cadet) -> Penalty | None:
    return with_served(Penalty.objects.filter(cadet=cadet, status=Penalty.Status.ACTIVE)).first()


def _reason_uz(reason_type: str) -> str:
    with translation.override("uz"):  # jurnal matni doim o'zbekcha
        return str(Penalty.Reason(reason_type).label)


@transaction.atomic
def add(cadet: Cadet, reason_type: str, note: str, order_date: dt.date, count: int, user) -> Penalty:
    """Zalyot kiritadi yoki faol zalyotga qo'shadi."""
    cadet = Cadet.objects.select_for_update().select_related("group").get(pk=cadet.pk)
    error = offender_error(cadet)
    if error:
        raise ServiceError(error)
    note = (note or "").strip()
    if not note:
        raise ServiceError(_("Izoh majburiy."))
    if reason_type not in Penalty.Reason.values:
        raise ServiceError(_("Sabab turi tanlanmagan."))
    if not (1 <= int(count) <= Penalty.MAX_ADD):
        raise ServiceError(_("Jazo naryadlari soni 1 dan 10 gacha bo‘lishi kerak."))
    count = int(count)
    penalty = Penalty.objects.select_for_update().filter(cadet=cadet, status=Penalty.Status.ACTIVE).first()
    if penalty is None:
        penalty = Penalty.objects.create(
            cadet=cadet, reason_type=reason_type, note=note, order_date=order_date, count=count, created_by=user
        )
        details = f"Yangi zalyot: {count} ta jazo naryadi (tanbeh {order_date:%d.%m.%Y})."
    else:
        penalty.count += count
        penalty.save(update_fields=["count"])
        details = f"Faol zalyotga qo‘shildi: +{count} ta (jami {penalty.count} ta; tanbeh {order_date:%d.%m.%Y})."
    ChangeLog.objects.create(
        action=ChangeLog.Action.PENALTY_ADD, cadet=cadet, user=user, reason=f"{_reason_uz(reason_type)}: {note}", details=details
    )
    return penalty


@transaction.atomic
def cancel(penalty: Penalty, reason: str, user) -> Penalty:
    penalty = Penalty.objects.select_for_update().get(pk=penalty.pk)
    if not penalty.is_active:
        raise ServiceError(_("Zalyot faol emas — bekor qilib bo‘lmaydi."))
    reason = (reason or "").strip()
    if not reason:
        raise ServiceError(_("Bekor qilish sababi majburiy."))
    penalty.status = Penalty.Status.CANCELLED
    penalty.cancel_reason = reason
    penalty.finished_at = timezone.now()
    penalty.save(update_fields=["status", "cancel_reason", "finished_at"])
    ChangeLog.objects.create(
        action=ChangeLog.Action.PENALTY_CANCEL, cadet=penalty.cadet, user=user, reason=reason,
        details=f"Zalyot bekor qilindi: {penalty.served} / {penalty.count} ta o‘tilgan edi.",
    )
    return penalty


def sync(penalty_ids: Iterable[int], user=None) -> None:
    """Tasdiqlash / tasdiqni bekor qilishdan keyin: soni tugasa — “bajarildi”, hisob qaytsa — yana “faol”."""
    for penalty in with_served(Penalty.objects.filter(pk__in=set(penalty_ids)).select_related("cadet")):
        if penalty.status == Penalty.Status.ACTIVE and penalty.served >= penalty.count:
            penalty.status = Penalty.Status.DONE
            penalty.finished_at = timezone.now()
            penalty.save(update_fields=["status", "finished_at"])
            ChangeLog.objects.create(
                action=ChangeLog.Action.PENALTY_DONE, cadet=penalty.cadet, user=user,
                details=f"Barcha {penalty.count} ta jazo naryadi o‘tildi — zalyot bajarildi.",
            )
        elif penalty.status == Penalty.Status.DONE and penalty.served < penalty.count:
            other = Penalty.objects.filter(cadet=penalty.cadet, status=Penalty.Status.ACTIVE).exclude(pk=penalty.pk).first()
            if other is not None:  # shu orada yangi faol zalyot ochilgan — qolgan naryad unga qo'shiladi
                other.count += penalty.count - penalty.served
                other.save(update_fields=["count"])
                penalty.count = penalty.served
                penalty.save(update_fields=["count"])
                details = f"Tasdiq bekor qilindi: qolgan jazo naryadi faol zalyotga qo‘shildi (jami {other.count} ta)."
            else:
                penalty.status = Penalty.Status.ACTIVE
                penalty.finished_at = None
                penalty.save(update_fields=["status", "finished_at"])
                details = f"Tasdiq bekor qilindi: {penalty.served} / {penalty.count} ta o‘tilgan — zalyot yana faol."
            ChangeLog.objects.create(action=ChangeLog.Action.PENALTY_RESUME, cadet=penalty.cadet, user=user, details=details)


def day_penalty_ids(duty_day: DutyDay) -> list[int]:
    return list(duty_day.assignments.filter(kind=Assignment.Kind.PENALTY).values_list("penalty_id", flat=True))


def engine_offenders(day: dt.date) -> list[em.Offender]:
    """Faol zalyotchiklar algoritm uchun: qolgan soni va oxirgi jazo joyi `day` dan oldingi tasdiqlanganlar bo'yicha."""
    penalties = list(Penalty.objects.filter(status=Penalty.Status.ACTIVE).order_by("pk"))
    if not penalties:
        return []
    approved = Assignment.objects.filter(
        kind=Assignment.Kind.PENALTY, duty_day__status=DutyDay.Status.APPROVED, duty_day__date__lt=day
    )
    served: dict[int, int] = {}
    for pid in approved.filter(penalty__in=penalties).values_list("penalty_id", flat=True):
        served[pid] = served.get(pid, 0) + 1
    last_post: dict[int, str] = {}
    cadet_ids = [p.cadet_id for p in penalties]
    for cid, code in (
        approved.filter(cadet_id__in=cadet_ids).order_by("duty_day__date").values_list("cadet_id", "post_slot__post__code")
    ):
        last_post[cid] = code  # oxirgisi qoladi
    return [
        em.Offender(cadet_id=p.cadet_id, since=p.order_date, remaining=p.count - served.get(p.pk, 0), last_post=last_post.get(p.cadet_id))
        for p in penalties
        if p.count - served.get(p.pk, 0) > 0
    ]


def active_offender_ids() -> set[int]:
    return set(Penalty.objects.filter(status=Penalty.Status.ACTIVE).values_list("cadet_id", flat=True))


# ---------------------------------------------------------------------------
# Forma (Zalyotchiklar sahifasi)
# ---------------------------------------------------------------------------


class PenaltyForm(forms.Form):
    cadet = forms.ModelChoiceField(queryset=Cadet.objects.none(), label=_lazy("Kursant"))
    reason_type = forms.ChoiceField(choices=Penalty.Reason.choices, label=_lazy("Sabab turi"))
    order_date = forms.DateField(
        label=_lazy("Buyruq/tanbeh sanasi"), widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
    )
    count = forms.IntegerField(label=_lazy("Jazo naryadlari soni"), min_value=1, max_value=Penalty.MAX_ADD, initial=1)
    note = forms.CharField(label=_lazy("Izoh"), max_length=500, widget=forms.TextInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Standart qoidalar: faqat o'g'il, faol, naryaddan ozod bo'lmagan kursantlar
        self.fields["cadet"].queryset = Cadet.objects.filter(
            gender=Gender.MALE, is_active=True, duty_exempt=False
        ).select_related("group").order_by("group__display_order", "last_name", "first_name")
        self.fields["cadet"].label_from_instance = lambda c: f"{c.group.code} · {c.full_name}"
        self.fields["cadet"].empty_label = _("— kursantni tanlang —")
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", INPUT_CLASS)
        self.fields["count"].widget.attrs.update({"inputmode": "numeric"})


class CancelForm(forms.Form):
    reason = forms.CharField(label=_lazy("Bekor qilish sababi"), max_length=500)
