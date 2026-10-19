"""18-bosqich: kasallik hujjatlari (rasmlar) — tekshirish, tozalash, himoyalangan ko'rish (CLAUDE.md 66-band)."""

from __future__ import annotations

import datetime as dt
import io
import json
import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from PIL import Image

from naryad import documents as doc_service
from naryad import services
from naryad.models import (
    Absence,
    Cadet,
    ChangeLog,
    DutyWeek,
    Gender,
    InitialRotation,
    Post,
    SickDocument,
    StudyGroup,
    User,
)

from .conftest import INITIAL_ROTATION

SUNDAY = dt.date(2026, 9, 13)
PASSWORD = "Kuchli-parol-2026"
ILLNESS = "Gripp, yuqori harorat"
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Rasm yasovchilar
# ---------------------------------------------------------------------------


def image_bytes(fmt: str = "JPEG", size=(120, 80), mode="RGB", exif=None) -> bytes:
    img = Image.new(mode, size, (200, 30, 30, 128) if mode == "RGBA" else (200, 30, 30))
    out = io.BytesIO()
    kwargs = {"exif": exif} if exif is not None else {}
    img.save(out, fmt, **kwargs)
    return out.getvalue()


def jpeg_bytes(size=(120, 80)) -> bytes:
    return image_bytes("JPEG", size)


def gps_exif(orientation: int = 6) -> bytes:
    exif = Image.Exif()
    exif[0x0112] = orientation  # 6 — 90° aylantirish kerak
    exif[0x010F] = "PhoneMaker"
    gps = exif.get_ifd(0x8825)
    gps[1], gps[2], gps[3], gps[4] = "N", (41.0, 18.0, 0.0), "E", (69.0, 15.0, 0.0)
    return exif.tobytes()


def upload(name: str, data: bytes, content_type: str = "image/jpeg") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, data, content_type=content_type)


# ---------------------------------------------------------------------------
# Muhit
# ---------------------------------------------------------------------------


@pytest.fixture
def world(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    DutyWeek.objects.create(start_date=SUNDAY)
    admin = User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")
    me, other = Cadet.objects.filter(gender=Gender.MALE, duty_exempt=False).order_by("pk")[:2]
    absence = Absence.objects.create(cadet=me, start_date=SUNDAY, end_date=SUNDAY + dt.timedelta(days=3), reason_type="kasal",
                                     illness=ILLNESS, created_by=admin)
    return {"admin": admin, "me": me, "other": other, "absence": absence,
            "me_user": User.objects.create_user("k1", password=PASSWORD, role="cadet", cadet=me),
            "other_user": User.objects.create_user("k2", password=PASSWORD, role="cadet", cadet=other)}


def post_upload(client, absence, data: bytes, name="rasm.jpg", kind="varaqa", note="", content_type="image/jpeg"):
    return client.post(reverse("sick_doc_upload", args=[absence.pk]),
                       {"image": upload(name, data, content_type), "kind": kind, "note": note}, follow=True)


# ---------------------------------------------------------------------------
# 1. Yuklash: qabul va rad
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("fmt, name, mode", [("JPEG", "a.jpg", "RGB"), ("PNG", "b.png", "RGBA"), ("WEBP", "c.webp", "RGB")])
def test_accepts_jpg_png_webp_and_stores_jpeg(client, world, fmt, name, mode):
    client.force_login(world["admin"])
    body = post_upload(client, world["absence"], image_bytes(fmt, (300, 200), mode), name).content.decode()
    assert "Hujjat yuklandi." in body
    doc = SickDocument.objects.with_bytes().get(absence=world["absence"])
    assert Image.open(io.BytesIO(bytes(doc.image))).format == "JPEG" and doc.size == len(bytes(doc.image))
    assert (doc.width, doc.height) == (300, 200)
    assert max(Image.open(io.BytesIO(bytes(doc.thumb))).size) <= doc_service.THUMB_SIDE


@pytest.mark.parametrize("name, data, content_type", [
    ("hujjat.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF", "application/pdf"),
    ("rasm.svg", b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>', "image/svg+xml"),
    ("sahifa.html", b"<html><body>salom</body></html>", "text/html"),
    ("soxta.jpg", b"MZ\x90\x00 bu exe, kengaytmasi o'zgartirilgan", "image/jpeg"),
    ("buzilgan.jpg", jpeg_bytes()[:60], "image/jpeg"),
])
def test_rejects_non_images_by_content(client, world, name, data, content_type):
    client.force_login(world["admin"])
    body = post_upload(client, world["absence"], data, name, content_type=content_type).content.decode()
    assert "Faqat rasm: JPG, PNG yoki WEBP." in body
    assert not SickDocument.objects.exists()


def test_rejects_heic_with_clear_message(client, world):
    client.force_login(world["admin"])
    heic = b"\x00\x00\x00\x18ftypheic\x00\x00\x00\x00mif1heic" + b"\x00" * 100
    assert "HEIC formati qo‘llab-quvvatlanmaydi" in post_upload(client, world["absence"], heic, "IMG_1.HEIC").content.decode()


def test_rejects_file_over_8_mb(client, world):
    client.force_login(world["admin"])
    big = jpeg_bytes() + b"\x00" * (8 * 1024 * 1024)
    assert "ko‘pi bilan 8 MB" in post_upload(client, world["absence"], big).content.decode()
    assert not SickDocument.objects.exists()


def test_sixth_image_rejected(client, world):
    client.force_login(world["admin"])
    for i in range(5):
        post_upload(client, world["absence"], jpeg_bytes(), f"{i}.jpg")
    assert SickDocument.objects.count() == 5
    body = post_upload(client, world["absence"], jpeg_bytes(), "6.jpg").content.decode()
    assert "ko‘pi bilan 5 ta rasm" in body and SickDocument.objects.count() == 5


def test_exif_gps_removed_orientation_applied_and_resized():
    full, _thumb, width, height = doc_service.process_image(image_bytes("JPEG", (4000, 3000), exif=gps_exif(6)))
    out = Image.open(io.BytesIO(full))
    assert (width, height) == out.size == (1500, 2000)  # aylantirildi (orientatsiya 6) va uzun tomoni 2000
    assert not out.getexif() and "exif" not in out.info
    assert b"PhoneMaker" not in full and b"GPS" not in full
    assert len(full) < len(image_bytes("JPEG", (4000, 3000), exif=gps_exif(6)))


def test_replace_and_delete_with_log_without_content(client, world):
    client.force_login(world["admin"])
    post_upload(client, world["absence"], jpeg_bytes((100, 100)), note="1-varaq")
    doc = SickDocument.objects.get()
    client.post(reverse("sick_doc_replace", args=[world["absence"].pk, doc.pk]), {"image": upload("y.png", image_bytes("PNG", (50, 70)))})
    doc = SickDocument.objects.with_bytes().get()
    assert (doc.width, doc.height) == (50, 70) and doc.note == "1-varaq"
    client.post(reverse("sick_doc_delete", args=[world["absence"].pk, doc.pk]))
    assert not SickDocument.objects.exists()
    logs = list(ChangeLog.objects.filter(action__startswith="doc_").order_by("pk"))
    assert [entry.action for entry in logs] == ["doc_add", "doc_replace", "doc_delete"]
    for entry in logs:
        assert entry.cadet == world["me"] and entry.user == world["admin"]
        assert entry.details == "Kasallik varaqasi: 13.09.2026–16.09.2026 yozuvi"  # rasm mazmuni yo'q


# ---------------------------------------------------------------------------
# 2. Ruxsat va sarlavhalar
# ---------------------------------------------------------------------------


def make_doc(absence, admin) -> SickDocument:
    full, thumb, w, h = doc_service.process_image(jpeg_bytes())
    return SickDocument.objects.create(absence=absence, image=full, thumb=thumb, width=w, height=h, size=len(full), created_by=admin)


def test_view_permissions_and_headers(client, world):
    doc = make_doc(world["absence"], world["admin"])
    url = reverse("sick_doc", args=[world["absence"].pk, doc.pk])
    response = client.get(url)
    assert response.status_code == 302 and reverse("login") in response["Location"]
    for user, expected in [(world["admin"], 200), (world["me_user"], 200), (world["other_user"], 403)]:
        client.force_login(user)
        response = client.get(url)
        assert response.status_code == expected, user
        if expected == 200:
            assert response["Content-Type"] == "image/jpeg"
            assert response["Cache-Control"] == "private, no-store"
            assert response["X-Content-Type-Options"] == "nosniff"
            assert response["X-Robots-Tag"].startswith("noindex")
            assert client.get(url + "?kichik=1").content == bytes(SickDocument.objects.with_bytes().get().thumb)
    # boshqa yozuvning id'si bilan — topilmaydi; URL'da tasodifiy UUID
    other_absence = Absence.objects.create(cadet=world["other"], start_date=SUNDAY, end_date=SUNDAY, reason_type="kasal")
    client.force_login(world["admin"])
    assert client.get(reverse("sick_doc", args=[other_absence.pk, doc.pk])).status_code == 404
    assert len(str(doc.pk)) == 36 and doc.pk.version == 4


def test_all_document_posts_forbidden_for_cadets(client, world):
    doc = make_doc(world["absence"], world["admin"])
    for user in (world["me_user"], world["other_user"]):
        client.force_login(user)
        assert client.post(reverse("sick_doc_upload", args=[world["absence"].pk]), {"image": upload("a.jpg", jpeg_bytes())}).status_code == 403
        assert client.post(reverse("sick_doc_replace", args=[world["absence"].pk, doc.pk]), {"image": upload("a.jpg", jpeg_bytes())}).status_code == 403
        assert client.post(reverse("sick_doc_delete", args=[world["absence"].pk, doc.pk])).status_code == 403
    assert SickDocument.objects.count() == 1


# ---------------------------------------------------------------------------
# 3. Kim nimani ko'radi
# ---------------------------------------------------------------------------


def test_cadet_sees_own_documents_without_illness(client, world, monkeypatch):
    from django.utils import timezone

    monkeypatch.setattr("django.utils.timezone.now", lambda: timezone.make_aware(dt.datetime.combine(dt.date(2026, 9, 14), dt.time(20))))
    doc = make_doc(world["absence"], world["admin"])
    client.force_login(world["me_user"])
    home = client.get(reverse("home")).content.decode()
    assert "Hujjatlaringiz: 1 ta" in home and ILLNESS not in home
    card = client.get(reverse("my_card"), follow=True).content.decode()
    assert "Hujjatlaringiz: 1 ta" in card and reverse("sick_doc", args=[world["absence"].pk, doc.pk]) in card
    assert ILLNESS not in card and reverse("sick_doc_delete", args=[world["absence"].pk, doc.pk]) not in card  # faqat ko'rish
    client.force_login(world["other_user"])
    for name in ("home", "approved_days"):
        html = client.get(reverse(name)).content.decode()
        assert "Hujjat" not in html and "sick_doc" not in html and str(doc.pk) not in html, name


def test_pdf_has_no_document_mark(client, world):
    from naryad import days

    make_doc(world["absence"], world["admin"])
    draft = services.generate_draft(SUNDAY, world["admin"])
    days.approve(SUNDAY, world["admin"], draft.version)
    client.force_login(world["other_user"])
    from pypdf import PdfReader

    text = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(client.get(reverse("day_pdf", args=[SUNDAY.isoformat()])).content)).pages)
    assert "hujjat" not in text.lower() and "kasal" not in text.lower()


def test_list_shows_count_and_missing_badge(client, world):
    make_doc(world["absence"], world["admin"])
    make_doc(world["absence"], world["admin"])
    empty = Absence.objects.create(cadet=world["other"], start_date=SUNDAY, end_date=SUNDAY + dt.timedelta(days=1), reason_type="kasal",
                                   illness="Angina", created_by=world["admin"])
    client.force_login(world["admin"])
    from django.utils import timezone

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("django.utils.timezone.now", lambda: timezone.make_aware(dt.datetime.combine(dt.date(2026, 9, 13), dt.time(20))))
        body = client.get(reverse("sick_list")).content.decode()
    assert re.search(rf'data-testid="docs-{world["absence"].pk}"[^>]*>📎 2 ', body) and f'data-testid="no-docs-{empty.pk}"' in body
    assert "Hujjat yo‘q" in body


def test_list_and_edit_pages_do_not_load_image_bytes(client, world):
    for _ in range(3):
        make_doc(world["absence"], world["admin"])
    client.force_login(world["admin"])
    for url in (reverse("sick_list") + "?holat=hammasi", reverse("sick_edit", args=[world["absence"].pk]), reverse("my_card")):
        with CaptureQueriesContext(connection) as ctx:
            client.get(url, follow=True)
        selects = [q["sql"] for q in ctx.captured_queries if "sick_document" in q["sql"]]
        assert all('"image"' not in sql and '"thumb"' not in sql for sql in selects), url


# ---------------------------------------------------------------------------
# 4. O'chirish va zaxira
# ---------------------------------------------------------------------------


def test_deleting_record_deletes_images_and_logs(client, world, monkeypatch):
    from django.utils import timezone

    future = Absence.objects.create(cadet=world["other"], start_date=SUNDAY + dt.timedelta(days=10), end_date=SUNDAY + dt.timedelta(days=11),
                                    reason_type="kasal", illness="x", created_by=world["admin"])
    make_doc(future, world["admin"])
    make_doc(future, world["admin"])
    monkeypatch.setattr("django.utils.timezone.now", lambda: timezone.make_aware(dt.datetime.combine(dt.date(2026, 9, 13), dt.time(20))))
    client.force_login(world["admin"])
    client.post(reverse("sick_delete", args=[future.pk]))
    assert not Absence.objects.filter(pk=future.pk).exists() and not SickDocument.objects.filter(absence_id=future.pk).exists()
    log = ChangeLog.objects.get(action="sick_delete", cadet=world["other"])
    assert "2 ta hujjat rasmi ham o‘chirildi" in log.details


def test_backup_includes_images_and_restores(world, tmp_path):
    doc = make_doc(world["absence"], world["admin"])
    original = bytes(SickDocument.objects.with_bytes().get(pk=doc.pk).image)
    dump = tmp_path / "zaxira.json"
    call_command("dumpdata", "naryad.sickdocument", output=str(dump), verbosity=0)
    data = json.loads(dump.read_text())
    assert len(data) == 1 and data[0]["fields"]["image"]  # baytlar zaxirada (base64)
    SickDocument.objects.all().delete()
    call_command("loaddata", str(dump), verbosity=0)
    assert bytes(SickDocument.objects.with_bytes().get(pk=doc.pk).image) == original


@pytest.mark.parametrize("lang, word", [("uz", "Hujjatlar"), ("ru", "Документы"), ("en", "Documents")])
def test_pages_open_in_three_languages(client, world, lang, word):
    make_doc(world["absence"], world["admin"])
    world["admin"].language = lang
    world["admin"].save()
    client.force_login(world["admin"])
    for url in (reverse("sick_list") + "?holat=hammasi", reverse("sick_edit", args=[world["absence"].pk]),
                reverse("cadet_detail", args=[world["me"].pk])):
        response = client.get(url)
        assert response.status_code == 200 and word in response.content.decode(), (lang, url)
