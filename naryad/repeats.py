"""Povtor — takroriy naryad (23-bosqich, CLAUDE.md 72-band).

Tasdiqlangan sutkada biror joy tarkibi kurs boshlig'idan e'tiroz olsa, admin (yoki kadir) shu joyni “povtor” deb
belgilaydi. Keyingi sutka tuzilganda shu tarkib xuddi o'sha joyga, o'sha lavozimlarda avtomatik qo'yiladi:

- povtor naryadi shaxsiy hisobga kirmaydi (Assignment.kind = repeat): adolat, saralash kaliti, statistika;
- povtor guruhi o'z joyida qoladi, shu joyga navbati kelgan guruh povtor guruhining navbatdagi joyiga o'tadi —
  uning bu joydagi navbati “o'tdi” (GroupPostAssignment.skipped_group), kursantlariga hech narsa yozilmaydi;
- keyingi sutkalarda guruhlar aylanishi amalda kim qayerda turganidan davom etadi;
- povtordagi kursantlar uchun “kecha turgan” cheklovi (QOIDA B) istisno;
- rasmiy PDF o'zgarmaydi.

Belgilash va bekor qilish faqat keyingi sutka hali tasdiqlanmagan bo'lsa; keyingi sutka qoralamasi bo'lsa, u
povtor bilan avtomatik qayta tuziladi. Hammasi jurnalga yoziladi.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from django.db import transaction
from django.utils.translation import gettext as _

from naryad.engine import models as em
from naryad.engine.config import ROTATION_CHAIN

from . import services
from .models import Assignment, ChangeLog, DutyDay, DutyWeek, GroupPostAssignment, Post, PostRepeat
from .services import ServiceError, StaleError, check_version

ONE_DAY = dt.timedelta(days=1)


def _source_rows(source_day: DutyDay, post: Post):
    """Povtorga qoldiriladigan tarkib: shu joydagi kursantlar (jazo o'rnidagi zalyotchiklarsiz)."""
    return (
        source_day.assignments.filter(post_slot__post=post)
        .exclude(kind=Assignment.Kind.PENALTY)
        .select_related("cadet", "post_slot")
        .order_by("post_slot__position")
    )


def engine_repeats(day: dt.date) -> list[em.RepeatPost]:
    """Shu sutka uchun povtorlar — oldingi (tasdiqlangan) sutkada belgilanganlar."""
    out = []
    qs = PostRepeat.objects.filter(
        source_day__date=day - ONE_DAY, source_day__status=DutyDay.Status.APPROVED
    ).select_related("post", "source_day")
    for r in qs:
        gpa = GroupPostAssignment.objects.filter(duty_day=r.source_day, post=r.post).select_related("group").first()
        out.append(
            em.RepeatPost(
                post=r.post.code,
                group=gpa.group.code if gpa else None,
                cadets=tuple((a.post_slot.position, a.cadet_id) for a in _source_rows(r.source_day, r.post)),
            )
        )
    return out


def expected_skipped_group(source_day: DutyDay, post: Post) -> str | None:
    """Keyingi sutkada shu joyga navbati keladigan guruh (zanjirda oldingi joydagi guruh) — jurnal uchun."""
    if post.code not in ROTATION_CHAIN:
        return None
    previous = ROTATION_CHAIN[ROTATION_CHAIN.index(post.code) - 1]
    gpa = GroupPostAssignment.objects.filter(duty_day=source_day, post__code=previous).select_related("group").first()
    return gpa.group.code if gpa else None


# ---------------------------------------------------------------------------
# Tekshiruvlar va ko'rinish
# ---------------------------------------------------------------------------


def mark_blocker(source_day: DutyDay | None, next_day: DutyDay | None | bool = False) -> str | None:
    """Povtorni belgilash / bekor qilish mumkin bo'lmasa — sababi (joriy tilda).
    `next_day` — keyingi sutka (allaqachon olingan bo'lsa; False — bazadan olinadi)."""
    if source_day is None or not source_day.is_approved:
        return _("Povtorni faqat tasdiqlangan sutkada belgilash mumkin.")
    next_date = source_day.date + ONE_DAY
    if next_day is False:
        next_day = DutyDay.objects.filter(date=next_date).first()
    if next_day is not None and next_day.is_approved:
        return _(
            "Keyingi sutka (%(day)s) tasdiqlangan — povtorni belgilash yoki bekor qilish uchun avval uning tasdig‘ini bekor qiling."
        ) % {"day": f"{next_date:%d.%m.%Y}"}
    next_week = services.week_start(next_date)
    if next_week != source_day.week.start_date and not DutyWeek.objects.filter(start_date=next_week).exists():
        return _(
            "Keyingi sutka (%(day)s) ochilgan 2-kurs haftasiga tegishli emas — povtor faqat keyingi sutkada turiladi."
        ) % {"day": f"{next_date:%d.%m.%Y}"}
    return None


def available_posts(source_day: DutyDay, marked_post_ids=None) -> list[Post]:
    """Povtor belgilash mumkin bo'lgan joylar: tarkibi bor va hali belgilanmagan."""
    if marked_post_ids is None:
        marked_post_ids = list(source_day.repeats.values_list("post_id", flat=True))
    with_cadets = source_day.assignments.exclude(kind=Assignment.Kind.PENALTY).values("post_slot__post_id")
    return list(Post.objects.filter(pk__in=with_cadets).exclude(pk__in=marked_post_ids).order_by("display_order"))


@dataclass
class RepeatInfo:
    repeat: PostRepeat
    group: str | None  # povtor guruhi (qizlarda None)
    skipped: str | None  # navbati o'tgan guruh (keyingi sutka tuzilgan bo'lsa)
    names: list[str]

    @property
    def text(self) -> str:
        values = {
            "post": _(self.repeat.post.name),
            "group": self.group or "",
            "day": f"{self.repeat.source_day.date:%d.%m}",
            "names": ", ".join(self.names),
        }
        if self.group:
            text = _("%(post)s: %(group)s guruhi (%(names)s) %(day)s sutkasidan povtorda — shaxsiy hisobga kirmaydi.") % values
        else:
            text = _("%(post)s: %(names)s %(day)s sutkasidan povtorda — shaxsiy hisobga kirmaydi.") % values
        if self.skipped:
            text += " " + _("%(group)s guruhining bu joydagi navbati o‘tdi.") % {"group": self.skipped}
        return text


def _info(r: PostRepeat, next_day: DutyDay | None) -> RepeatInfo:
    gpa = GroupPostAssignment.objects.filter(duty_day=r.source_day, post=r.post).select_related("group").first()
    skipped = None
    if next_day is not None:
        next_gpa = (
            GroupPostAssignment.objects.filter(duty_day=next_day, post=r.post, is_repeat=True)
            .select_related("skipped_group")
            .first()
        )
        skipped = next_gpa.skipped_group.code if next_gpa and next_gpa.skipped_group else None
    names = [a.cadet.short_name for a in _source_rows(r.source_day, r.post)]
    return RepeatInfo(r, gpa.group.code if gpa else None, skipped, names)


def page_context(date: dt.date, duty_day: DutyDay | None, can_mark: bool) -> dict:
    """Sutka sahifasi (admin) uchun:
    - repeats_here — oldingi sutkada belgilangan, shu sutkada turiladigan povtorlar;
    - repeats_marked / repeat_blocker / repeat_posts — tasdiqlangan sutkada povtor belgilash paneli."""
    rows = list(PostRepeat.objects.filter(source_day__date__in=[date - ONE_DAY, date]).select_related("post", "source_day"))
    here = [r for r in rows if r.source_day.date != date]
    marked = [r for r in rows if r.source_day.date == date]
    context = {"repeats_here": [_info(r, duty_day) for r in here]}
    if duty_day is not None and duty_day.is_approved and can_mark:
        next_day = DutyDay.objects.filter(date=date + ONE_DAY).first()
        context["repeats_marked"] = [_info(r, next_day) for r in marked]
        context["repeat_blocker"] = mark_blocker(duty_day, next_day)
        context["repeat_posts"] = available_posts(duty_day, [r.post_id for r in marked]) if not context["repeat_blocker"] else []
    return context


# ---------------------------------------------------------------------------
# O'zgartiruvchi amallar
# ---------------------------------------------------------------------------


def _lock_source(date: dt.date, expected_version) -> DutyDay:
    duty_day = DutyDay.objects.select_for_update().filter(date=date).first()
    if duty_day is None:
        raise StaleError()
    check_version(duty_day, expected_version)
    blocker = mark_blocker(duty_day)
    if blocker:
        raise ServiceError(blocker)
    return duty_day


def _refresh_next(source_day: DutyDay, user) -> bool:
    """Keyingi sutka qoralamasi bo'lsa — povtor bilan qayta tuziladi. Qayta tuzilgan bo'lsa True."""
    next_day = DutyDay.objects.filter(date=source_day.date + ONE_DAY, status=DutyDay.Status.DRAFT).first()
    if next_day is None:
        return False
    services.generate_draft(next_day.date, user)
    return True


@transaction.atomic
def mark(date: dt.date, post_id: int, reason: str, user, expected_version=None) -> bool:
    """Joyni povtor deb belgilaydi. Keyingi sutka qoralamasi qayta tuzilgan bo'lsa True qaytaradi."""
    source_day = _lock_source(date, expected_version)
    reason = (reason or "").strip()
    if not reason:
        raise ServiceError(_("Povtor sababi majburiy."))
    post = Post.objects.filter(pk=post_id).first()
    if post is None:
        raise ServiceError(_("Joyni tanlang."))
    if PostRepeat.objects.filter(source_day=source_day, post=post).exists():
        raise ServiceError(_("Bu joy uchun povtor allaqachon belgilangan."))
    rows = list(_source_rows(source_day, post))
    if not rows:
        raise ServiceError(_("Bu joyda povtorga qoldiriladigan kursant yo‘q."))
    PostRepeat.objects.create(source_day=source_day, post=post, reason=reason, created_by=user)

    # Jurnal — saqlanadigan matn, doim o'zbekcha
    gpa = GroupPostAssignment.objects.filter(duty_day=source_day, post=post).select_related("group").first()
    who = f"{gpa.group.code} guruhi" if gpa else "Tarkib"
    names = ", ".join(a.cadet.short_name for a in rows)
    details = f"{post.name}: {who} ({names}) {date + ONE_DAY:%d.%m.%Y} sutkasida povtorda turadi (shaxsiy hisobga kirmaydi)."
    if skipped := expected_skipped_group(source_day, post):
        details += f" {skipped} guruhining bu joydagi navbati o‘tadi."
    ChangeLog.objects.create(duty_day=source_day, action=ChangeLog.Action.REPEAT_ADD, reason=reason, user=user, details=details)
    return _refresh_next(source_day, user)


@transaction.atomic
def cancel(date: dt.date, repeat_id: int, reason: str, user, expected_version=None) -> bool:
    """Povtorni bekor qiladi. Keyingi sutka qoralamasi qayta tuzilgan bo'lsa True qaytaradi."""
    source_day = _lock_source(date, expected_version)
    reason = (reason or "").strip()
    if not reason:
        raise ServiceError(_("Povtorni bekor qilish sababi majburiy."))
    repeat = source_day.repeats.select_related("post").filter(pk=repeat_id).first()
    if repeat is None:
        raise StaleError()
    details = f"{repeat.post.name}: {date + ONE_DAY:%d.%m.%Y} sutkasidagi povtor bekor qilindi."
    repeat.delete()
    ChangeLog.objects.create(duty_day=source_day, action=ChangeLog.Action.REPEAT_CANCEL, reason=reason, user=user, details=details)
    return _refresh_next(source_day, user)


def drop_on_reopen(source_day: DutyDay, reason: str, user) -> None:
    """Sutka tasdig'i bekor qilinsa, unda belgilangan povtorlar ham bekor bo'ladi (tarkib o'zgarishi mumkin)."""
    for repeat in source_day.repeats.select_related("post"):
        ChangeLog.objects.create(
            duty_day=source_day, action=ChangeLog.Action.REPEAT_CANCEL, user=user,
            reason=f"Sutka tasdig‘i bekor qilindi: {reason}",
            details=f"{repeat.post.name}: {source_day.date + ONE_DAY:%d.%m.%Y} sutkasidagi povtor bekor qilindi.",
        )
        repeat.delete()
