"""Testlar uchun umumiy ma'lumotlar: haqiqiy 100 kishilik ro'yxat va simulyatsiya."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

import pytest

from naryad.engine import generate_day
from naryad.engine.models import Cadet, Record

ROSTER_PATH = Path(__file__).resolve().parents[1] / "data" / "roster.json"

# 2026-09-13 — yakshanba, 2-kurs haftasining 1-sutkasi
WEEK_START = dt.date(2026, 9, 13)

# Birinchi sutka uchun admin kiritadigan boshlang'ich taqsimot
INITIAL_ROTATION = {
    "markaz": "BI-625",
    "noj1": "BI-525",
    "noj2": "BI-425",
    "yotoq1": "BI-225",
    "oquv": "BI-325",
    "patrul": "YuP-125",
}


def load_roster() -> list[Cadet]:
    """Algoritm testlari uchun nomzodlar hovuzi: naryaddan ozodlar kirmaydi (services.engine_cadets kabi)."""
    data = [c for c in json.loads(ROSTER_PATH.read_text(encoding="utf-8")) if not c.get("duty_exempt")]
    return [
        Cadet(
            id=c["id"],
            last_name=c["last_name"],
            first_name=c["first_name"],
            patronymic=c["patronymic"],
            group=c["group"],
            gender=c["gender"],
            short_name=c["short_name"],
        )
        for c in data
    ]


def simulate(cadets, start: dt.date, days: int, history=None, absences=(), initial_rotation=INITIAL_ROTATION):
    """`days` sutkani ketma-ket tuzadi; har sutka "tasdiqlanib" tarixga qo'shiladi."""
    history: list[Record] = list(history or [])
    results = []
    for i in range(days):
        day = start + dt.timedelta(days=i)
        res = generate_day(day, cadets, history, absences, initial_rotation=initial_rotation)
        results.append(res)
        history.extend(res.to_records())
    return results, history


@pytest.fixture(scope="session")
def cadets() -> list[Cadet]:
    return load_roster()


@pytest.fixture(scope="session")
def week(cadets):
    """Bo'sh tarixdan boshlangan 7 sutkalik hafta."""
    return simulate(cadets, WEEK_START, 7)


# ---------------------------------------------------------------------------
# Django (pytest-django) uchun umumiy fixture'lar
# ---------------------------------------------------------------------------

GROUPS = [
    ("YuP-125", "Yurisprudensiya", "uz"),
    ("BI-225", "Bojxona ishi", "uz"),
    ("BI-325", "Bojxona ishi", "uz"),
    ("BI-425", "Bojxona ishi", "uz"),
    ("BI-525", "Bojxona ishi", "uz"),
    ("BI-625", "Bojxona ishi", "ru"),
]


@pytest.fixture
def db_groups(db):
    from naryad.models import StudyGroup

    return {
        code: StudyGroup.objects.create(code=code, direction=direction, language=lang, display_order=i)
        for i, (code, direction, lang) in enumerate(GROUPS, start=1)
    }


@pytest.fixture
def db_cadets(db_groups):
    """roster.json dagi 100 kursant bazaga yoziladi (id'lar ro'yxatdagidek)."""
    from naryad.models import Cadet

    from django.core.management.color import no_style
    from django.db import connection

    data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    cadets = [
        Cadet.objects.create(
            pk=c["id"],
            group=db_groups[c["group"]],
            last_name=c["last_name"],
            first_name=c["first_name"],
            patronymic=c["patronymic"],
            gender=c["gender"],
            list_number=c["list_number"],
            duty_exempt=c.get("duty_exempt", False),
            duty_position=c.get("duty_position", ""),
        )
        for c in data
    ]
    # id'lar qo'lda berildi — PostgreSQL sanog'ini (sequence) oldinga suramiz
    with connection.cursor() as cursor:
        for sql in connection.ops.sequence_reset_sql(no_style(), [Cadet]):
            cursor.execute(sql)
    return cadets


# 16-bosqich: “ozod” yozuvi sahifalardan olib tashlandi (uch tilda). Kursant ismlari (masalan, Ozodbek) hisobga olinmaydi.
# 21-bosqich (5a): “Naryadga chiqmaydi” ham olib tashlandi — faqat lavozim nomi qoladi.
EXEMPT_WORD = re.compile(
    r"\w*(?:ozod|освобожд|exempt)\w*|naryadga chiqmaydi\w*|не заступа\w* в наряд|not on the duty roster", re.IGNORECASE
)


def exempt_words(html: str) -> set[str]:
    """Sahifada ko‘rinadigan matn (va title/aria-label) ichidagi “ozod” so‘zlari — ismlardan tashqari."""
    from naryad.models import Cadet as CadetModel

    html = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.DOTALL)
    attrs = " ".join(re.findall(r'(?:title|aria-label|placeholder)="([^"]*)"', html))
    text = re.sub(r"<[^>]+>", " ", html) + " " + attrs
    names = " ".join(" ".join(n) for n in CadetModel.objects.values_list("last_name", "first_name", "patronymic")).lower()
    return {w for w in EXEMPT_WORD.findall(text) if w.lower() not in names}
