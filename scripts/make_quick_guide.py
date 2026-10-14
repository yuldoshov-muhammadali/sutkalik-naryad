"""Bir sahifalik qisqa yo'riqnoma: docs/qollanma/qisqa-yoriqnoma.html -> .pdf (WeasyPrint).

    python scripts/make_quick_guide.py
"""

from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
src = ROOT / "docs" / "qollanma" / "qisqa-yoriqnoma.html"
out = src.with_suffix(".pdf")
doc = HTML(filename=str(src)).render()
doc.write_pdf(str(out))
print(f"{out.relative_to(ROOT)}: {len(doc.pages)} sahifa")
