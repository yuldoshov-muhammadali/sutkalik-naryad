"""locale/**/django.po -> django.mo (GNU gettext/msgfmt kerak emas, polib ishlatiladi).

Ishga tushirish: python scripts/compile_messages.py
(msgfmt o'rnatilgan bo'lsa, `python manage.py compilemessages` ham ishlaydi.)
"""

from pathlib import Path

import polib

ROOT = Path(__file__).resolve().parents[1]

for po_path in sorted((ROOT / "locale").glob("*/LC_MESSAGES/*.po")):
    po = polib.pofile(str(po_path))
    mo_path = po_path.with_suffix(".mo")
    po.save_as_mofile(str(mo_path))
    print(f"{po_path.relative_to(ROOT)} -> {mo_path.relative_to(ROOT)} ({len(po.translated_entries())} ta tarjima)")
