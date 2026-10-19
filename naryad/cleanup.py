"""Sinov ma'lumotlarini to'liq tozalash (20-bosqich, CLAUDE.md 69-band) — hamma narsa 0 dan.

O'chadi: haftalar, sutkalar (qoralama va tasdiqlangan, import qilingan tarix ham), guruh → joy taqsimotlari,
naryadlar (oddiy va jazo), e'lon qilingan naryadlar, zalyotlar va ularning kiritishlari, butun jurnal.
Qoladi: kursantlar, guruhlar, joylar, foydalanuvchilar, sozlamalar, boshlang'ich taqsimot, lavozimlar,
sababli holatlar va kasallar ro'yxati (hujjatlari bilan).

Tartib: ko'rib chiqish → ikki so'z bilan tasdiq → AVTOMATIK zaxira (muvaffaqiyatsiz bo'lsa o'chirish boshlanmaydi)
→ bitta tranzaksiyada o'chirish → jurnalda bitta yozuv “Sinov ma'lumotlari tozalandi”.
"""

from __future__ import annotations

import gzip
import hashlib
import io
from dataclasses import dataclass, field
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.translation import gettext as _

from .models import (
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    GroupPostAssignment,
    Penalty,
    PenaltyEntry,
    PublishedDuty,
)

WORD_1 = "TOZALASH"
WORD_2 = "HAMMASI NOL"


class CleanupError(Exception):
    pass


@dataclass
class Preview:
    weeks: int = 0
    days: int = 0
    days_approved: int = 0
    days_draft: int = 0
    days_imported: int = 0
    assignments: int = 0
    assignments_penalty: int = 0
    group_posts: int = 0
    published: int = 0
    penalties: int = 0
    penalty_entries: int = 0
    changelog: int = 0
    cadets: list = field(default_factory=list)  # (kursant, oldin, keyin=0)

    @property
    def days_platform(self) -> int:
        return self.days - self.days_imported

    @property
    def nothing_to_delete(self) -> bool:
        return not (self.weeks or self.days or self.assignments or self.penalties or self.published) and self.only_log_left

    @property
    def only_log_left(self) -> bool:
        """Faqat avvalgi tozalash yozuvi qolgan bo'lsa — o'chiradigan narsa yo'q."""
        return self.changelog == ChangeLog.objects.filter(action=ChangeLog.Action.TEST_DATA_CLEARED).count()

    @property
    def token(self) -> str:
        """Holat izi: ko'rib chiqilgandan keyin baza o'zgarsa yoki allaqachon tozalangan bo'lsa — qayta o'chirilmaydi."""
        raw = f"{self.weeks}:{self.days}:{self.assignments}:{self.penalties}:{self.penalty_entries}:{self.changelog}:{self.published}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


def preview() -> Preview:
    """Hech narsani o'zgartirmaydi: nima o'chishini sanaydi."""
    imported = set(ChangeLog.objects.filter(action=ChangeLog.Action.IMPORT).values_list("day_date", flat=True))
    p = Preview(
        weeks=DutyWeek.objects.count(),
        days=DutyDay.objects.count(),
        days_approved=DutyDay.objects.filter(status=DutyDay.Status.APPROVED).count(),
        days_draft=DutyDay.objects.filter(status=DutyDay.Status.DRAFT).count(),
        days_imported=DutyDay.objects.filter(date__in=imported).count(),
        assignments=Assignment.objects.count(),
        assignments_penalty=Assignment.objects.filter(kind=Assignment.Kind.PENALTY).count(),
        group_posts=GroupPostAssignment.objects.count(),
        published=PublishedDuty.objects.count(),
        penalties=Penalty.objects.count(),
        penalty_entries=PenaltyEntry.objects.count(),
        changelog=ChangeLog.objects.count(),
    )
    counts = Cadet.objects.annotate(
        n=Count("assignments", filter=Q(assignments__duty_day__status=DutyDay.Status.APPROVED, assignments__kind=Assignment.Kind.NORMAL))
    ).select_related("group").order_by("group__display_order", "last_name", "first_name")
    p.cadets = [(c, c.n, 0) for c in counts]
    return p


def backup_dir() -> Path:
    return Path(getattr(settings, "BACKUP_DIR", Path(settings.BASE_DIR) / "data" / "zaxira"))


def make_backup(directory: Path | None = None) -> Path:
    """To'liq baza nusxasi (Django fixture, .json.gz), nomi soniyalarigacha. Tiklash: `loaddata`. Xato bo'lsa — CleanupError."""
    directory = Path(directory or backup_dir())
    try:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"zaxira_{timezone.localtime():%Y-%m-%d_%H-%M-%S}.json.gz"
        buffer = io.StringIO()
        call_command(
            "dumpdata", natural_foreign=True, indent=None, stdout=buffer,
            exclude=["contenttypes", "auth.permission", "sessions", "admin.logentry"],
        )
        data = buffer.getvalue()
        if not data.startswith("[") or len(data) < 10:
            raise CleanupError(_("Zaxira bo‘sh chiqdi."))
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            fh.write(data)
        if path.stat().st_size == 0:
            raise CleanupError(_("Zaxira fayli yozilmadi."))
        return path
    except CleanupError:
        raise
    except Exception as exc:  # disk, ruxsat, serializatsiya — o'chirish boshlanmaydi
        raise CleanupError(_("Zaxira olinmadi: %(error)s") % {"error": exc}) from exc


@dataclass
class Result:
    deleted: dict
    backup: Path


def clear(user, word_1: str, word_2: str, token: str, backup_to: Path | None = None) -> Result:
    """Ikki so'z + ko'rib chiqish izi bilan. Avval zaxira, keyin bitta tranzaksiyada o'chirish."""
    if (word_1 or "").strip() != WORD_1 or (word_2 or "").strip() != WORD_2:
        raise CleanupError(_("Tasdiqlash so‘zlari noto‘g‘ri — hech narsa o‘chirilmadi."))
    current = preview()
    if current.token != token:
        raise CleanupError(_("Ko‘rib chiqilgandan keyin ma’lumot o‘zgargan yoki allaqachon tozalangan — qayta ko‘rib chiqing."))
    if current.nothing_to_delete:
        raise CleanupError(_("O‘chiradigan sinov ma’lumoti yo‘q — allaqachon tozalangan."))
    backup = make_backup(backup_to)
    with transaction.atomic():
        deleted = {
            "assignments": Assignment.objects.all().delete()[0],
            "group_posts": GroupPostAssignment.objects.all().delete()[0],
            "published": PublishedDuty.objects.all().delete()[0],
            "penalty_entries": PenaltyEntry.objects.all().delete()[0],
            "penalties": Penalty.objects.all().delete()[0],
            "days": DutyDay.objects.all().delete()[0],
            "weeks": DutyWeek.objects.all().delete()[0],
            "changelog": ChangeLog.objects.all().delete()[0],
        }
        ChangeLog.objects.create(
            action=ChangeLog.Action.TEST_DATA_CLEARED, user=user,
            details=(
                f"O‘chirildi: {current.weeks} hafta, {current.days} sutka ({current.days_imported} tasi import qilingan), "
                f"{current.assignments} naryad yozuvi, {current.penalties} zalyot, {current.changelog} jurnal yozuvi. "
                f"Zaxira: {backup.name}"
            ),
        )
    return Result(deleted=deleted, backup=backup)
