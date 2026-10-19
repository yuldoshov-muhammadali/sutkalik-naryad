"""18-bosqich: platforma nomi E-NARYAD (CLAUDE.md 65-band). PDF naryad shakli o'zgarmaydi."""

from __future__ import annotations

import datetime as dt
import io
import re

import pytest
from django.conf import settings
from django.template.loader import render_to_string
from django.urls import reverse
from pypdf import PdfReader

from naryad import days, services
from naryad.models import Cadet, DutyWeek, InitialRotation, Post, StudyGroup, User

from .conftest import INITIAL_ROTATION

SUNDAY = dt.date(2026, 9, 13)
pytestmark = pytest.mark.django_db

# Eski nomning ko'rinadigan shakllari (uch tilda). “sutkalik naryad” hujjat ma'nosida (ro'yxat, PDF) qoladi.
OLD_NAMES = [
    "Sutkalik naryad —", ">Sutkalik naryad<", "— 2-kurs</title>", "2-kurs sutkalik naryad", "sutkalik naryad platformasi",
    "Суточный наряд —", ">Суточный наряд<", "Суточный наряд 2-го курса", "платформа суточного наряда", "— 2-й курс</title>",
    "Daily duty roster —", ">Daily duty roster<", "2nd-year daily duty roster", "daily duty roster platform", "— 2nd year</title>",
]


@pytest.fixture
def world(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    DutyWeek.objects.create(start_date=SUNDAY)
    admin = User.objects.create_user("kursboshligi", password="Kuchli-parol-2026", role="admin")
    draft = services.generate_draft(SUNDAY, admin)
    days.approve(SUNDAY, admin, draft.version)
    cadet = User.objects.create_user("kursant", password="Kuchli-parol-2026", role="cadet", cadet=Cadet.objects.first())
    return {"admin": admin, "cadet": cadet}


def check_page(html: str, where: str) -> None:
    title = re.search(r"<title>(.*?)</title>", html, re.DOTALL).group(1).strip()
    assert title.endswith("E-NARYAD"), (where, title)
    for old in OLD_NAMES:
        assert old not in html, (where, old)


@pytest.mark.parametrize("lang", ["uz", "ru", "en"])
def test_main_pages_show_new_name_in_three_languages(client, world, lang):
    client.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
    login = client.get(reverse("login")).content.decode()
    check_page(login, "login")
    assert 'data-testid="site-name">E-NARYAD<' in login
    for role in ("admin", "cadet"):
        user = world[role]
        user.language = lang
        user.save()
        client.force_login(user)
        pages = ["home", "approved_days", "my_card"] if role == "cadet" else ["home", "week_list", "cadet_list", "stats", "sick_list", "penalty_list", "absence_list"]
        for name in pages:
            html = client.get(reverse(name), follow=True).content.decode()
            check_page(html, f"{role}:{name}")
            assert 'data-testid="site-name">E-NARYAD<' in html, (role, name)
        day = client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()
        check_page(day, f"{role}:day")
        client.logout()


def test_admin_home_hero_and_error_pages(client, world):
    client.force_login(world["admin"])
    home = client.get(reverse("home")).content.decode()
    assert re.search(r'id="hero-title"[^>]*>E-NARYAD<', home)
    assert "E-NARYAD" in client.get("/admin/").content.decode()
    forbidden = client.get(reverse("my_card"))  # admin uchun 403 sahifasi
    assert forbidden.status_code == 403 and "E-NARYAD" in forbidden.content.decode()
    missing = client.get("/yoq-sahifa/")
    assert missing.status_code == 404 and "E-NARYAD" in missing.content.decode()
    server_error = render_to_string("500.html")
    assert "<title>" in server_error and "E-NARYAD" in server_error and "Sutkalik naryad" not in server_error


def test_name_is_defined_once():
    assert settings.SITE_NAME == "E-NARYAD"
    from naryad.admin_site import NaryadAdminSite

    assert NaryadAdminSite.site_title == "E-NARYAD" and str(NaryadAdminSite.site_header).startswith("E-NARYAD")


def test_pdf_form_unchanged_metadata_has_name(client, world):
    client.force_login(world["admin"])
    content = client.get(reverse("day_pdf", args=[SUNDAY.isoformat()])).content
    reader = PdfReader(io.BytesIO(content))
    text = "\n".join(p.extract_text() for p in reader.pages)
    assert len(reader.pages) == 1
    assert "2026-yil 13-sentabr kunidan 14-sentabr kuniga sutkalik naryadlar ro‘yxati" in text.replace("\n", " ")
    assert "E-NARYAD" not in text and "Kurs boshlig‘i" in text  # shakl matnida yangi nom yo'q
    assert reader.metadata.title == "Sutkalik naryadlar ro‘yxati" and reader.metadata.creator == "E-NARYAD"


def test_accounts_excel_title_uses_new_name(world, tmp_path):
    from openpyxl import load_workbook

    from naryad import accounts

    path = accounts.write_accounts_xlsx([], tmp_path, dt.date(2026, 9, 13))
    assert load_workbook(path).active["A1"].value == "E-NARYAD — kursant akkauntlari (13.09.2026)"
