"""8-bosqich: PDF (rasmiy shakl), chop etish, qoralamani o'chirish."""

from __future__ import annotations

import datetime as dt
import io
import shutil
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import call_command
from django.urls import reverse
from pypdf import PdfReader

from naryad import days, pdf, services
from naryad.engine.allocator import week_start
from naryad.models import Assignment, Cadet, ChangeLog, DutyDay, DutyWeek, InitialRotation, Post, StudyGroup, User

from .conftest import INITIAL_ROTATION

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "data" / "tarix_namuna.xlsx"
SEPT_18 = dt.date(2026, 9, 18)
PASSWORD = "Kuchli-parol-2026"
pytestmark = pytest.mark.django_db


def pdf_text(content: bytes) -> tuple[int, str]:
    reader = PdfReader(io.BytesIO(content))
    return len(reader.pages), "\n".join(p.extract_text() for p in reader.pages)


@pytest.fixture
def admin(db_cadets):
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


@pytest.fixture
def sept18(db_cadets):
    call_command("import_history", str(SAMPLE), stdout=StringIO())
    return DutyDay.objects.get(date=SEPT_18)


@pytest.fixture
def rotation(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))


def cadet_client(client):
    user = User.objects.create_user("k", password=PASSWORD, role="cadet", cadet=Cadet.objects.first())
    client.force_login(user)
    return client


# ---------------------------------------------------------------------------
# Rasmiy shakl
# ---------------------------------------------------------------------------


def test_approved_day_pdf_one_page_with_all_names_title_and_signature(sept18):
    pages, text = pdf_text(pdf.render_pdf([sept18]))
    assert pages == 1
    names = [a.cadet.short_name for a in sept18.assignments.select_related("cadet")]
    assert len(names) == 20
    for name in names:
        assert name in text, name
    assert "2026-yil 18-sentabr kunidan 19-sentabr kuniga sutkalik naryadlar ro‘yxati" in text
    assert "2-kurs ro‘yxati" in text
    assert "Bojxona instituti Navbatchilik" in text and "qismi boshlig‘i, podpolkovnik" in text and "X.Sattorovga" in text
    assert "Kurs boshlig‘i" in text and "mayor" in text and "X.Turobov" in text
    assert "QORALAMA" not in text


def test_uzbek_letters_and_digraph_initials_are_intact(sept18):
    _, text = pdf_text(pdf.render_pdf([sept18]))
    for fragment in ["G‘ayratov G‘", "Sa’dullayev B", "Shavkatov Sh", "Mexmonov Sh", "G‘iyozov I",
                     "1-NO‘J bo‘yicha navbatchi", "O‘quv binosi bo‘yicha posbon", "Kurs bo‘yicha navbatchi"]:
        assert fragment in text, fragment
    assert "?" not in text and "�" not in text


def test_row_labels_and_section_order(sept18):
    _, text = pdf_text(pdf.render_pdf([sept18]))
    order = ["Markaz bo‘yicha navbatchi yordamchisi", "1-NO‘J bo‘yicha", "2-NO‘J bo‘yicha", "1-Yotoqxona bo‘yicha",
             "O‘quv binosi bo‘yicha", "Institut bo‘yicha patrul", "Qizlar yotoqxonasi bo‘yicha"]
    positions = [text.index(t) for t in order]
    assert positions == sorted(positions)
    assert text.count("Institut bo‘yicha patrul") == 2  # bo'lim sarlavhasi + faqat 1-qator
    assert text.count("Kurs bo‘yicha posbon") == 2
    assert "Markaz bo‘yicha\n" not in text  # Markazda bo'lim sarlavhasi yo'q


@pytest.mark.parametrize(
    "day, expected",
    [
        (dt.date(2026, 9, 18), "2026-yil 18-sentabr kunidan 19-sentabr kuniga sutkalik naryadlar ro‘yxati"),
        (dt.date(2026, 12, 31), "2026-yil 31-dekabr kunidan 2027-yil 1-yanvar kuniga sutkalik naryadlar ro‘yxati"),
        (dt.date(2027, 1, 31), "2027-yil 31-yanvar kunidan 1-fevral kuniga sutkalik naryadlar ro‘yxati"),
        (dt.date(2028, 2, 28), "2028-yil 28-fevral kunidan 29-fevral kuniga sutkalik naryadlar ro‘yxati"),
    ],
)
def test_title_month_names_and_year_change(day, expected):
    assert pdf.title_for(day) == expected


def test_year_change_title_in_pdf(rotation, admin):
    day = dt.date(2026, 12, 31)
    DutyWeek.objects.create(start_date=week_start(day))
    duty_day = services.generate_draft(day, admin)
    _, text = pdf_text(pdf.render_pdf([duty_day]))
    assert "2026-yil 31-dekabr kunidan 2027-yil 1-yanvar kuniga" in text


def test_draft_pdf_has_watermark(rotation, admin):
    DutyWeek.objects.create(start_date=dt.date(2026, 9, 13))
    draft = services.generate_draft(dt.date(2026, 9, 13), admin)
    pages, text = pdf_text(pdf.render_pdf([draft]))
    assert pages == 1 and "QORALAMA" in text
    days.approve(draft.date, admin, draft.version)
    draft.refresh_from_db()
    _, text = pdf_text(pdf.render_pdf([draft]))
    assert "QORALAMA" not in text


def test_draft_pdf_shows_empty_slot(rotation, admin):
    DutyWeek.objects.create(start_date=dt.date(2026, 9, 13))
    draft = services.generate_draft(dt.date(2026, 9, 13), admin)
    Assignment.objects.filter(duty_day=draft, post_slot__post__code="patrul", post_slot__position=4).delete()
    _, text = pdf_text(pdf.render_pdf([draft]))
    assert "— bo‘sh —" in text


# ---------------------------------------------------------------------------
# Yuklab olish, ruxsatlar, fayl nomlari
# ---------------------------------------------------------------------------


def test_download_and_filename(client, sept18, admin):
    client.force_login(admin)
    resp = client.get(reverse("day_pdf", args=["2026-09-18"]))
    assert resp.status_code == 200 and resp["Content-Type"] == "application/pdf"
    assert resp["Content-Disposition"] == 'attachment; filename="naryad_2026-09-18.pdf"'
    assert resp.content.startswith(b"%PDF")
    resp = client.get(reverse("day_pdf", args=["2026-09-18"]) + "?inline=1")
    assert resp["Content-Disposition"].startswith("inline;")


def test_cadet_gets_no_pdf(client, sept18, rotation, admin):
    """14-bosqich: PDF’da butun ro'yxat bor — kursantga yopiq (tasdiqlangan ham, qoralama ham)."""
    cadet_client(client)
    assert client.get(reverse("day_pdf", args=["2026-09-18"])).status_code == 403
    assert client.get(reverse("day_print", args=["2026-09-18"])).status_code == 403
    services.generate_draft(dt.date(2026, 9, 19), admin)
    assert client.get(reverse("day_pdf", args=["2026-09-19"])).status_code == 403
    client.logout()
    resp = client.get(reverse("day_pdf", args=["2026-09-18"]))
    assert resp.status_code == 302 and resp["Location"].startswith(reverse("login"))


def test_admin_gets_draft_pdf(client, sept18, admin):
    services.generate_draft(dt.date(2026, 9, 19), admin)
    client.force_login(admin)
    resp = client.get(reverse("day_pdf", args=["2026-09-19"]))
    assert resp.status_code == 200
    assert "QORALAMA" in pdf_text(resp.content)[1]


def test_week_pdf_pages_and_permissions(client, sept18, admin):
    services.generate_draft(dt.date(2026, 9, 19), admin)  # 18 tasdiqlangan + 19 qoralama
    client.force_login(admin)
    resp = client.get(reverse("week_pdf", args=["2026-09-13"]))
    assert resp["Content-Disposition"] == 'attachment; filename="naryad_hafta_2026-09-13.pdf"'
    pages, text = pdf_text(resp.content)
    assert pages == 2 and "18-sentabr kunidan" in text and "19-sentabr kunidan" in text
    cadet_client(client)
    assert client.get(reverse("week_pdf", args=["2026-09-13"])).status_code == 403  # 14-bosqich


def test_print_page_embeds_pdf(client, sept18, admin):
    client.force_login(admin)
    body = client.get(reverse("day_print", args=["2026-09-18"])).content.decode()
    assert "/sutka/2026-09-18/pdf/?inline=1" in body and "js/print.js" in body
    assert "<script>" not in body and "onclick" not in body  # CSP: inline JavaScript yo'q
    script = (Path(__file__).resolve().parents[1] / "static" / "js" / "print.js").read_text()
    assert ".print()" in script
    # PDF chop etish oynasidagi iframe ichida ochiladi — faqat shu javob SAMEORIGIN
    pdf = client.get(reverse("day_pdf", args=["2026-09-18"]) + "?inline=1")
    assert pdf["X-Frame-Options"] == "SAMEORIGIN"


def test_day_page_has_pdf_buttons(client, sept18, admin):
    client.force_login(admin)
    body = client.get(reverse("day_detail", args=["2026-09-18"])).content.decode()
    assert "PDF yuklab olish" in body and "Chop etish" in body


# ---------------------------------------------------------------------------
# Shrift
# ---------------------------------------------------------------------------


def test_font_fallback_and_times_new_roman(tmp_path, monkeypatch, sept18):
    monkeypatch.setattr(pdf, "FONT_DIR", tmp_path)
    assert pdf.active_font_name() == "Liberation Serif"
    assert pdf.font_faces()[0] == ""
    # "times.ttf" qo'yilsa — o'sha ishlatiladi (test uchun Liberation fayli nusxasi)
    source = Path("/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf")
    if not source.exists():
        pytest.skip("Liberation Serif o'rnatilmagan")
    shutil.copy(source, tmp_path / "times.ttf")
    assert pdf.active_font_name() == "Times New Roman"
    faces, family = pdf.font_faces()
    assert "times.ttf" in faces and family.startswith('"NaryadTimes"')
    pages, text = pdf_text(pdf.render_pdf([sept18]))
    assert pages == 1 and "G‘ayratov G‘" in text


# ---------------------------------------------------------------------------
# Qoralamani o'chirish
# ---------------------------------------------------------------------------


def test_delete_latest_draft_requires_reason_and_keeps_log(client, sept18, admin):
    draft = services.generate_draft(dt.date(2026, 9, 19), admin)
    with pytest.raises(services.ServiceError, match="sababi majburiy"):
        days.delete_draft(draft.date, " ", admin, draft.version)
    client.force_login(admin)
    resp = client.post(reverse("day_delete", args=["2026-09-19"]), {"reason": "noto‘g‘ri sana", "version": draft.version})
    assert resp.status_code == 302
    assert not DutyDay.objects.filter(date=draft.date).exists()
    assert not Assignment.objects.filter(duty_day_id=draft.pk).exists()
    log = ChangeLog.objects.filter(day_date=draft.date).order_by("id")
    assert [e.action for e in log] == ["generate", "draft_delete"]
    assert log.last().reason == "noto‘g‘ri sana"
    body = client.get(reverse("day_log", args=["2026-09-19"])).content.decode()
    assert "Qoralama o‘chirildi" in body and "noto‘g‘ri sana" in body


def test_only_latest_draft_can_be_deleted(sept18, rotation, admin):
    with pytest.raises(services.ServiceError, match="Tasdiqlangan sutkani o‘chirib bo‘lmaydi"):
        days.delete_draft(SEPT_18, "sabab", admin, sept18.version)
    draft = services.generate_draft(dt.date(2026, 9, 19), admin)
    # sun'iy holat: undan keyin yana sutka bor
    later_week = DutyWeek.objects.create(start_date=dt.date(2026, 9, 27))
    DutyDay.objects.create(week=later_week, date=dt.date(2026, 9, 27))
    with pytest.raises(services.ServiceError, match="Faqat eng oxirgi qoralamani"):
        days.delete_draft(draft.date, "sabab", admin, draft.version)
    assert DutyDay.objects.filter(pk=draft.pk).exists()


def test_deleting_draft_unblocks_reopen_of_previous_day(sept18, admin):
    draft = services.generate_draft(dt.date(2026, 9, 19), admin)
    sept18.refresh_from_db()
    with pytest.raises(services.ServiceError, match="Keyingi sutka"):
        days.reopen(SEPT_18, "xato", admin, sept18.version)
    days.delete_draft(draft.date, "18-sentabrni tuzatish kerak", admin, draft.version)
    days.reopen(SEPT_18, "xato", admin, sept18.version)
    sept18.refresh_from_db()
    assert sept18.status == "draft"


def test_cadet_cannot_delete_draft(client, sept18, admin):
    draft = services.generate_draft(dt.date(2026, 9, 19), admin)
    cadet_client(client)
    assert client.post(reverse("day_delete", args=["2026-09-19"]), {"reason": "x", "version": draft.version}).status_code == 403
    assert DutyDay.objects.filter(pk=draft.pk).exists()
