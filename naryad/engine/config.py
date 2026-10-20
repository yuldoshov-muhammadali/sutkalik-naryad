"""Qat'iy konfiguratsiya: 7 joy, 20 o'rin, lavozimlar va aylanish zanjiri.

CLAUDE.md 3-bo'lim. Joylar va o'rinlar soni hech kim tomonidan o'zgartirilmaydi.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from .models import FEMALE, MALE, ROLE_ASSISTANT, ROLE_DUTY, ROLE_GUARD, Post, Slot

# Sutka va hafta chegarasi (mahalliy vaqt, Asia/Tashkent)
DUTY_START_TIME = dt.time(18, 0)


def _slots(post: str, items: list[tuple[str, str, bool]]) -> tuple[Slot, ...]:
    return tuple(
        Slot(post=post, position=i, role=role, pdf_label=label, show_label=show)
        for i, (role, label, show) in enumerate(items, start=1)
    )


MARKAZ = Post(
    code="markaz",
    name="Markaz bo‘yicha",
    section_title="Markaz bo‘yicha",
    gender=MALE,
    display_order=1,
    rotation_index=0,
    slots=_slots(
        "markaz",
        [(ROLE_ASSISTANT, "Markaz bo‘yicha navbatchi yordamchisi", True)],
    ),
)

NOJ1 = Post(
    code="noj1",
    name="1-NO‘J bo‘yicha",
    section_title="1-NO‘J bo‘yicha",
    gender=MALE,
    display_order=2,
    rotation_index=1,
    slots=_slots(
        "noj1",
        [
            (ROLE_DUTY, "1-NO‘J bo‘yicha navbatchi", True),
            (ROLE_ASSISTANT, "1-NO‘J bo‘yicha navbatchi yordamchisi", True),
            (ROLE_GUARD, "1-NO‘J bo‘yicha posbon", True),
            (ROLE_GUARD, "1-NO‘J bo‘yicha posbon", True),
        ],
    ),
)

NOJ2 = Post(
    code="noj2",
    name="2-NO‘J bo‘yicha",
    section_title="2-NO‘J bo‘yicha",
    gender=MALE,
    display_order=3,
    rotation_index=2,
    slots=_slots(
        "noj2",
        [
            (ROLE_DUTY, "2-NO‘J bo‘yicha navbatchi", True),
            (ROLE_GUARD, "2-NO‘J bo‘yicha posbon", True),
            (ROLE_GUARD, "2-NO‘J bo‘yicha posbon", True),
        ],
    ),
)

YOTOQ1 = Post(
    code="yotoq1",
    name="1-Yotoqxona bo‘yicha",
    section_title="1-Yotoqxona bo‘yicha",
    gender=MALE,
    display_order=4,
    rotation_index=3,
    slots=_slots(
        "yotoq1",
        [
            (ROLE_DUTY, "Kurs bo‘yicha navbatchi", True),
            (ROLE_GUARD, "Kurs bo‘yicha posbon", True),
            (ROLE_GUARD, "Kurs bo‘yicha posbon", True),
        ],
    ),
)

OQUV = Post(
    code="oquv",
    name="O‘quv binosi bo‘yicha",
    section_title="O‘quv binosi bo‘yicha",
    gender=MALE,
    display_order=5,
    rotation_index=4,
    slots=_slots(
        "oquv",
        [
            (ROLE_DUTY, "O‘quv binosi bo‘yicha navbatchi", True),
            (ROLE_GUARD, "O‘quv binosi bo‘yicha posbon", True),
        ],
    ),
)

PATRUL = Post(
    code="patrul",
    name="Institut bo‘yicha patrul",
    section_title="Institut bo‘yicha patrul",
    gender=MALE,
    display_order=6,
    rotation_index=5,
    slots=_slots(
        "patrul",
        [
            (ROLE_GUARD, "Institut bo‘yicha patrul", True),
            (ROLE_GUARD, "Institut bo‘yicha patrul", False),
            (ROLE_GUARD, "Institut bo‘yicha patrul", False),
            (ROLE_GUARD, "Institut bo‘yicha patrul", False),
        ],
    ),
)

QIZLAR = Post(
    code="qizlar",
    name="Qizlar yotoqxonasi bo‘yicha",
    section_title="Qizlar yotoqxonasi bo‘yicha",
    gender=FEMALE,
    display_order=7,
    rotation_index=None,
    slots=_slots(
        "qizlar",
        [
            (ROLE_DUTY, "Qizlar yotoqxonasi bo‘yicha navbatchi", True),
            (ROLE_GUARD, "Qizlar yotoqxonasi bo‘yicha posbon", True),
            (ROLE_GUARD, "Qizlar yotoqxonasi bo‘yicha posbon", True),
        ],
    ),
)

# PDF tartibida barcha joylar
POSTS: tuple[Post, ...] = (MARKAZ, NOJ1, NOJ2, YOTOQ1, OQUV, PATRUL, QIZLAR)
POSTS_BY_CODE: dict[str, Post] = {p.code: p for p in POSTS}

# Aylanish zanjiri: Markaz → 1-NO‘J → 2-NO‘J → 1-Yotoqxona → O‘quv binosi → Patrul → Markaz
ROTATION_CHAIN: tuple[str, ...] = tuple(
    p.code for p in sorted((p for p in POSTS if p.rotation_index is not None), key=lambda p: p.rotation_index)
)
MALE_POSTS: tuple[Post, ...] = tuple(POSTS_BY_CODE[c] for c in ROTATION_CHAIN)
FEMALE_POST: Post = QIZLAR

# Zalyotchiklar (15-bosqich): jazo naryadi faqat shu ikki joyda, posbon o'rnida
PENALTY_POSTS: tuple[str, ...] = (NOJ1.code, YOTOQ1.code)
PENALTY_ROLE = ROLE_GUARD
PENALTY_PER_POST_DEFAULT = 1  # bir sutkada bitta joyga ko'pi bilan (Sozlamalarda o'zgaradi)

# 21-bosqich: joylar navbati va og'ir joylar (Sozlamalarda yoqiladi; o'chiq bo'lsa — eski tartib, bayt-bayt)
HARD_POSTS_DEFAULT: tuple[str, ...] = (NOJ1.code, YOTOQ1.code)
# Tsikl: Markaz (1 kishi) kirmaydi; kursant 5 ta katta joyning hammasida turmaguncha bittasini takrorlamaslikka harakat
CYCLE_POSTS: tuple[str, ...] = tuple(c for c in ROTATION_CHAIN if c != MARKAZ.code)


@dataclass(frozen=True)
class PostRotation:
    """Joylar navbati qoidalari (21-bosqich). `generate_day(..., rotation=None)` — eski tartib.

    QOIDA A: 2-kurs haftasida (yakshanba 18:00 – yakshanba 18:00) bitta kursant ko'pi bilan BITTA og'ir joyda;
    faqat guruhda kishi yetmasa yumshatiladi (o'rin bo'sh qolmasin) va ogohlantirish yoziladi.
    Faqat ODDIY naryadlar hisoblanadi; jazo naryadlari QOIDA A, tsikl va og'ir joylar soniga kirmaydi.
    """

    hard_posts: tuple[str, ...] = HARD_POSTS_DEFAULT
    cycle_posts: tuple[str, ...] = CYCLE_POSTS


TOTAL_SLOTS = sum(p.size for p in POSTS)
MALE_SLOTS = sum(p.size for p in MALE_POSTS)
FEMALE_SLOTS = FEMALE_POST.size


def _self_check() -> None:
    """Konfiguratsiya CLAUDE.md 3-bo'lim bilan mosligini import paytida tekshiradi."""
    sizes = {p.code: p.size for p in POSTS}
    expected = {"markaz": 1, "noj1": 4, "noj2": 3, "yotoq1": 3, "oquv": 2, "patrul": 4, "qizlar": 3}
    if sizes != expected:
        raise RuntimeError(f"Joylar hajmi CLAUDE.md bilan mos emas: {sizes}")
    if (MALE_SLOTS, FEMALE_SLOTS, TOTAL_SLOTS) != (17, 3, 20):
        raise RuntimeError("O'rinlar soni 17 + 3 = 20 bo'lishi kerak")


_self_check()
