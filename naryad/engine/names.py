"""Ism-familiyalar bilan ishlash: belgilarni birxillashtirish va PDF uchun qisqa shakl.

CLAUDE.md 5-bo'lim (qisqa shakl) va 10-bo'lim, 3-band (belgilar).
"""

from __future__ import annotations

import re

OKINA = "\u2018"  # ‘ — o‘, g‘ uchun (U+2018)
TUTUQ = "\u2019"  # ’ — tutuq belgisi: Sa’dullayev (U+2019)

# Manba fayllarda uchraydigan barcha apostrof ko'rinishlari
_APOSTROPHES = "'`´‘’\u02bb\u02bcʹ"  # manbalarda uchraydigan barcha ko'rinishlar
_APOS_CLASS = "[" + re.escape(_APOSTROPHES) + "]"


def normalize_apostrophes(text: str) -> str:
    """o/g dan keyingi apostrofni ‘ ga, qolganlarini ’ ga keltiradi (CLAUDE.md 10-bo'lim, 3-band).

    Qoraqalpoqcha harflar (ǵ, í, á) o'zgarmaydi.
    """
    return re.sub(
        "(.?)" + _APOS_CLASS,
        lambda m: m.group(1) + (OKINA if m.group(1) in {"O", "o", "G", "g"} and m.group(1) else TUTUQ),
        text,
    )


def first_letter(name: str) -> str:
    """Ismning bosh harfi; ikki harfli tovushlar saqlanadi: Sh, Ch, G‘, O‘."""
    name = normalize_apostrophes(name.strip())
    if not name:
        return ""
    head = name[:2]
    if head[:1].upper() in {"S", "C"} and head[1:2].lower() == "h":
        return head[0].upper() + "h"
    if head[:1].upper() in {"G", "O"} and head[1:2] == OKINA:
        return head[0].upper() + OKINA
    return name[0].upper()


def short_name(last_name: str, first_name: str) -> str:
    """PDF uchun qisqa shakl: Familiya + ism bosh harfi (Shavkatov Sh, G‘ayratov G‘)."""
    return f"{normalize_apostrophes(last_name.strip())} {first_letter(first_name)}"
