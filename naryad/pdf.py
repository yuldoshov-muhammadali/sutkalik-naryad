"""Rasmiy shakldagi PDF (A4, Times New Roman) — CLAUDE.md 5-bo'lim, 8-bosqich.

Shrift: loyiha ildizidagi `fonts/times.ttf` (va `timesbd.ttf`) bo'lsa — o'sha
(Times New Roman litsenziyali, shuning uchun repozitoriyda yo'q, .gitignore'da);
bo'lmasa o'lchamlari aynan bir xil Liberation Serif (Docker'da `fonts-liberation`).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string

from .days import sections
from .models import DutyDay, Setting

MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]
FONT_DIR = Path(settings.BASE_DIR) / "fonts"


def uz_day(day: dt.date) -> str:
    return f"{day.day}-{MONTHS[day.month - 1]}"


def title_for(day: dt.date) -> str:
    """'2026-yil 18-sentabr kunidan 19-sentabr kuniga sutkalik naryadlar ro‘yxati' (yil almashsa — ikkalasida yil)."""
    nxt = day + dt.timedelta(days=1)
    if nxt.year == day.year:
        span = f"{day.year}-yil {uz_day(day)} kunidan {uz_day(nxt)} kuniga"
    else:
        span = f"{day.year}-yil {uz_day(day)} kunidan {nxt.year}-yil {uz_day(nxt)} kuniga"
    return f"{span} sutkalik naryadlar ro‘yxati"


def font_faces() -> tuple[str, str]:
    """(@font-face CSS, font-family ro'yxati). Times New Roman fayli bo'lsa — birinchi o'rinda."""
    faces = []
    regular, bold = FONT_DIR / "times.ttf", FONT_DIR / "timesbd.ttf"
    if regular.exists():
        faces.append(f'@font-face {{ font-family: "NaryadTimes"; src: url("{regular.as_uri()}"); font-weight: normal; }}')
        if bold.exists():
            faces.append(f'@font-face {{ font-family: "NaryadTimes"; src: url("{bold.as_uri()}"); font-weight: bold; }}')
    family = '"NaryadTimes", "Times New Roman", "Liberation Serif", "Tinos", serif'
    return "\n".join(faces), family


def active_font_name() -> str:
    return "Times New Roman" if (FONT_DIR / "times.ttf").exists() else "Liberation Serif"


def page_context(duty_day: DutyDay) -> dict:
    return {
        "duty_day": duty_day,
        "title": title_for(duty_day.date),
        "sections": sections(duty_day),
        "draft": not duty_day.is_approved,
    }


def render_html(days: list[DutyDay]) -> str:
    setting = Setting.load()
    faces, family = font_faces()
    return render_to_string(
        "naryad/pdf/naryad.html",
        {
            "pages": [page_context(d) for d in days],
            "setting": setting,
            "recipient_lines": [line.strip() for line in setting.recipient_position.splitlines() if line.strip()],
            "font_faces": faces,
            "font_family": family,
        },
    )


def render_pdf(days: list[DutyDay]) -> bytes:
    from weasyprint import HTML
    from weasyprint.text.fonts import FontConfiguration

    html = render_html(days)
    font_config = FontConfiguration()
    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf(font_config=font_config)


def day_filename(day: dt.date) -> str:
    return f"naryad_{day.isoformat()}.pdf"


def week_filename(start: dt.date) -> str:
    return f"naryad_hafta_{start.isoformat()}.pdf"
