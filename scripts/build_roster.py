"""data/2-KURS ROYXATI.doc -> data/roster.json

Ishga tushirish (loyiha ildizidan):
    python scripts/build_roster.py
    python scripts/build_roster.py --txt royxat.txt   # .doc allaqachon matnga aylantirilgan bo'lsa

.doc ni o'qish uchun LibreOffice (`soffice`) kerak. Jins faylda yozilmagan:
CLAUDE.md 2-bo'limidagi 13 ta qiz familiyasi bo'yicha belgilanadi va otasining
ismi qo'shimchasi (qizi / -ovna / -evna) bilan qo'shimcha tekshiriladi.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from naryad.engine.names import normalize_apostrophes, short_name  # noqa: E402

DOC_PATH = ROOT / "data" / "2-KURS ROYXATI.doc"
OUT_PATH = ROOT / "data" / "roster.json"

GIRL_SURNAMES = {
    "Abduvaliyeva", "Shamsiddinova", "Abdullayeva", "Karimova", "Quvatova", "Mamirova", "Zoirova",
    "Baxtiyorova", "Panjiyeva", "Azizova", "Maxmudova", "Muxammadiyeva", "Ordabaeva",
}
EXPECTED = {  # CLAUDE.md 2-bo'lim: guruh -> (o'g'il, qiz)
    "YuP-125": (13, 2), "BI-225": (14, 3), "BI-325": (14, 2),
    "BI-425": (15, 2), "BI-525": (17, 0), "BI-625": (14, 4),
}
# Otasining ismidan keyin keladigan alohida so'zlar (o'zbekcha va qoraqalpoqcha)
PATRONYMIC_WORDS = {"o‘g‘li", "qizi", "uǵli", "ulí"}


def doc_to_text(doc: Path) -> str:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("LibreOffice (soffice) topilmadi. .doc ni o'zingiz matnga aylantirib, --txt bilan bering.")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "royxat.doc"
        shutil.copy(doc, src)
        subprocess.run(
            [soffice, "--headless", "--convert-to", "txt:Text (encoded):UTF8", "--outdir", tmp, str(src)],
            check=True,
            capture_output=True,
            timeout=180,
        )
        return (Path(tmp) / "royxat.txt").read_text(encoding="utf-8")


def split_name(full: str) -> tuple[str, str, str]:
    """'Familiya Ism Otasining ismi [o‘g‘li]' -> (familiya, ism, otasining ismi)."""
    tokens = normalize_apostrophes(full).split()
    last = tokens[0]
    rest = tokens[1:]
    if len(rest) >= 3 and rest[-1] in PATRONYMIC_WORDS:
        return last, " ".join(rest[:-2]), " ".join(rest[-2:])
    if len(rest) >= 2:
        return last, " ".join(rest[:-1]), rest[-1]
    return last, " ".join(rest), ""


def parse(text: str) -> list[dict]:
    lines = [line.strip() for line in text.splitlines()]
    cadets: list[dict] = []
    group = None
    for i, line in enumerate(lines):
        m = re.search(r"(YUP-125|BI-\d25)", line, re.IGNORECASE)
        if m and "nalishi" in line:
            group = m.group(1).upper().replace("YUP", "YuP")
            continue
        if group and re.fullmatch(r"\d+\.", line) and i + 1 < len(lines):
            full = normalize_apostrophes(lines[i + 1])
            last, first, patronymic = split_name(full)
            female_by_name = last in GIRL_SURNAMES
            female_by_suffix = bool(re.search(r"(qizi|ovna|evna)$", full))
            if female_by_name != female_by_suffix:
                sys.exit(f"Jins aniqlanmadi (familiya va qo'shimcha mos emas): {full}")
            cadets.append(
                {
                    "id": len(cadets) + 1,
                    "list_number": int(line[:-1]),
                    "group": group,
                    "last_name": last,
                    "first_name": first,
                    "patronymic": patronymic,
                    "full_name": full,
                    "gender": "F" if female_by_name else "M",
                    "short_name": short_name(last, first),
                }
            )
    return cadets


# Naryaddan ozod (komandirlar va kurs lavozimlari) — CLAUDE.md 2-bo'lim, 10-bo'lim 56-band.
# Guruh + to'liq F.I.Sh. bo'yicha aniq topiladi; topilmasa yoki bir nechta mos kelsa — to'xtaydi.
EXEMPT = {
    ("YuP-125", "Abduqodirov Abdulqosim Abdulxakim o‘g‘li"): "Kurs starshinasi",
    ("YuP-125", "Tojiyev Sherali Tolmas o‘g‘li"): "YuP-125 guruh komandiri",
    ("BI-225", "Eshmatov Jobirbek Baxtiyor o‘g‘li"): "BI-225 guruh komandiri",
    ("BI-225", "Bo‘riyev Shohruxmirzo Norbobo o‘g‘li"): "Kurs pisari",
    ("BI-325", "Akramjonov Axmadjon Akramjon o‘g‘li"): "BI-325 guruh komandiri",
    ("BI-325", "Xayrillayev Javohir Oybek o‘g‘li"): "Kaptyorchik",
    ("BI-425", "Navro‘zov Jasurbek Baxtiyor o‘g‘li"): "BI-425 guruh komandiri",
    ("BI-525", "Abdulazizov Oyatillo Abduxalilovich"): "BI-525 guruh komandiri",
    ("BI-625", "O‘rmonjonov Muxammadqodir Jaxongir o‘g‘li"): "BI-625 guruh komandiri",
}


def mark_exempt(cadets: list[dict]) -> None:
    for c in cadets:
        c["duty_exempt"] = False
        c["duty_position"] = ""
    for (group, full), position in EXEMPT.items():
        matches = [c for c in cadets if c["group"] == group and c["full_name"] == full]
        if len(matches) != 1:
            sys.exit(f"Naryaddan ozod kursant aniq topilmadi: {group} {full} ({len(matches)} ta mos)")
        matches[0]["duty_exempt"] = True
        matches[0]["duty_position"] = position


def check(cadets: list[dict]) -> None:
    for group, (boys, girls) in EXPECTED.items():
        got_b = sum(1 for c in cadets if c["group"] == group and c["gender"] == "M")
        got_g = sum(1 for c in cadets if c["group"] == group and c["gender"] == "F")
        if (got_b, got_g) != (boys, girls):
            sys.exit(f"{group}: kutilgan {boys}/{girls}, ro'yxatda {got_b}/{got_g}")
    if len(cadets) != 100:
        sys.exit(f"Jami 100 kishi kutilgan, topildi: {len(cadets)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--txt", type=Path, help=".doc dan olingan UTF-8 matn fayli")
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args()

    text = args.txt.read_text(encoding="utf-8") if args.txt else doc_to_text(DOC_PATH)
    cadets = parse(text)
    check(cadets)
    mark_exempt(cadets)
    args.out.write_text(json.dumps(cadets, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(cadets)} kursant yozildi: {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}")


if __name__ == "__main__":
    main()
