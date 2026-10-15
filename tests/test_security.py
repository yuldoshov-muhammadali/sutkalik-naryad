"""10-bosqich: ruxsatlar auditi (har bir URL × rol), xavfsizlik sarlavhalari, /health/, yuklash cheklovlari."""

from __future__ import annotations

import datetime as dt
import io

import pytest
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import timezone
from openpyxl import Workbook

from naryad import cadet_import, services
from naryad.models import Absence, Cadet, DutyDay, DutyWeek, Gender, InitialRotation, Post, StudyGroup, User

from .conftest import INITIAL_ROTATION

PASSWORD = "Kuchli-parol-2026"
SUNDAY = dt.date(2026, 9, 13)
MONDAY = SUNDAY + dt.timedelta(days=1)
pytestmark = pytest.mark.django_db


@pytest.fixture
def world(db_cadets):
    """Bitta tasdiqlangan sutka (yakshanba), bitta qoralama (dushanba), ikki kursant akkaunti."""
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    admin = User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")
    DutyWeek.objects.create(start_date=SUNDAY)
    approved = services.generate_draft(SUNDAY, admin)
    from naryad import days

    days.approve(SUNDAY, admin, approved.version)
    draft = services.generate_draft(MONDAY, admin)
    me, other = Cadet.objects.filter(gender=Gender.MALE).order_by("pk")[:2]
    cadet = User.objects.create_user("kursant", password=PASSWORD, role="cadet", cadet=me)
    absence = Absence.objects.create(cadet=other, start_date=MONDAY, end_date=MONDAY, reason_type="kasal", created_by=admin)
    slot = draft.assignments.select_related("post_slot").first().post_slot
    from naryad import penalties

    penalty = penalties.add(other, "tartib", "Kechikib keldi", SUNDAY, 2, admin)
    return {"admin": admin, "cadet": cadet, "me": me, "other": other, "draft": draft, "slot": slot, "absence": absence,
            "penalty": penalty}


def urls(w) -> dict[str, str]:
    """Har bir nomli URL uchun namunaviy manzil (yangi URL qo'shilsa — shu yerga ham qo'shing)."""
    s, m = SUNDAY.isoformat(), MONDAY.isoformat()
    return {
        "home": reverse("home"),
        "home_status": reverse("home_status"),
        "set_language": reverse("set_language"),
        "login": reverse("login"),
        "logout": reverse("logout"),
        "password_change": reverse("password_change"),
        "cadet_list": reverse("cadet_list"),
        "cadet_create": reverse("cadet_create"),
        "cadet_short_name": reverse("cadet_short_name") + "?last_name=Aliyev&first_name=Vali",
        "cadet_import": reverse("cadet_import"),
        "cadet_import_template": reverse("cadet_import_template"),
        "cadet_detail:own": reverse("cadet_detail", args=[w["me"].pk]),
        "cadet_detail:other": reverse("cadet_detail", args=[w["other"].pk]),
        "cadet_edit": reverse("cadet_edit", args=[w["other"].pk]),
        "cadet_deactivate": reverse("cadet_deactivate", args=[w["other"].pk]),
        "cadet_activate": reverse("cadet_activate", args=[w["other"].pk]),
        "cadet_exempt": reverse("cadet_exempt", args=[w["other"].pk]),
        "cadet_unexempt": reverse("cadet_unexempt", args=[w["other"].pk]),
        "my_card": reverse("my_card"),
        "week_list": reverse("week_list"),
        "week_open": reverse("week_open"),
        "week_preview": reverse("week_preview") + "?start=2026-09-20",
        "approved_days": reverse("approved_days"),
        "day_detail:approved": reverse("day_detail", args=[s]),
        "day_detail:draft": reverse("day_detail", args=[m]),
        "day_generate": reverse("day_generate", args=[m]),
        "day_replace": reverse("day_replace", args=[m, w["slot"].pk]),
        "day_swap": reverse("day_swap", args=[m, w["slot"].post_id]),
        "day_approve": reverse("day_approve", args=[m]),
        "day_reopen": reverse("day_reopen", args=[s]),
        "day_log": reverse("day_log", args=[s]),
        "day_delete": reverse("day_delete", args=[m]),
        "day_pdf:approved": reverse("day_pdf", args=[s]),
        "day_pdf:draft": reverse("day_pdf", args=[m]),
        "day_print:approved": reverse("day_print", args=[s]),
        "day_print:draft": reverse("day_print", args=[m]),
        "week_pdf": reverse("week_pdf", args=[s]),
        "absence_list": reverse("absence_list"),
        "penalty_list": reverse("penalty_list"),
        "penalty_cancel": reverse("penalty_cancel", args=[w["penalty"].pk]),
        "absence_end": reverse("absence_end", args=[w["absence"].pk]),
        "absence_delete": reverse("absence_delete", args=[w["absence"].pk]),
        "stats": reverse("stats"),
        "stats_excel": reverse("stats_excel"),
    }


# Kursant uchun kutilgan GET natijasi: 200 — ochiladi, 302 — yo'naltiriladi, 403/404/405 — yopiq.
CADET_GET = {
    "home": 200,
    "home_status": 200,  # bosh sahifa holat kartochkalari (HTMX)
    "login": 302,  # kirgan foydalanuvchi bosh sahifaga
    "password_change": 200,
    "cadet_detail:own": 200,
    "my_card": 302,
    # 14-bosqich: kursant boshqa kursantlarning ro'yxatini ko'rmaydi — sutka sahifalari va PDF yopiq
    "approved_days": 403,
    "day_detail:approved": 403,
    "day_pdf:approved": 403,
    "day_print:approved": 403,
    "week_pdf": 403,
    "day_detail:draft": 403,
    "day_pdf:draft": 403,
    "day_print:draft": 403,
    "logout": 405,  # faqat POST
}
PUBLIC = {"login"}
# Faqat POST qabul qiladigan manzillar: GET so'rovi hamma uchun 405 (ruxsat POST'da tekshiriladi)
POST_ONLY = {"logout", "set_language", "penalty_cancel", "cadet_deactivate", "cadet_activate", "cadet_exempt", "cadet_unexempt", "week_open", "day_generate", "day_approve", "day_reopen",
             "day_delete", "absence_end", "absence_delete"}


def all_url_names() -> set[str]:
    names = set()

    def walk(patterns):
        for p in patterns:
            if isinstance(p, URLResolver):
                if p.namespace != "admin":
                    walk(p.url_patterns)
            elif isinstance(p, URLPattern) and p.name:
                names.add(p.name)

    walk(get_resolver().url_patterns)
    return names


def test_every_url_is_covered_by_audit(world):
    covered = {key.split(":")[0] for key in urls(world)}
    assert all_url_names() == covered


def test_anonymous_is_sent_to_login_everywhere(client, world):
    for key, url in urls(world).items():
        response = client.get(url)
        if key in PUBLIC:
            assert response.status_code == 200, key
        elif key in POST_ONLY:
            assert response.status_code == 405, key
        else:
            assert response.status_code == 302 and response["Location"].startswith(reverse("login")), key


def test_cadet_sees_only_what_is_allowed(client, world):
    client.force_login(world["cadet"])
    for key, url in urls(world).items():
        expected = 405 if key in POST_ONLY else CADET_GET.get(key, 403)
        assert client.get(url).status_code == expected, (key, url)


def test_cadet_cannot_change_anything_by_post(client, world):
    client.force_login(world["cadet"])
    draft = DutyDay.objects.get(date=MONDAY)
    for key in ["cadet_create", "cadet_import", "cadet_edit", "cadet_deactivate", "cadet_activate", "cadet_exempt",
                "cadet_unexempt", "week_open",
                "day_generate", "day_replace", "day_swap", "day_approve", "day_reopen", "day_delete",
                "absence_list", "absence_end", "absence_delete"]:
        response = client.post(urls(world)[key], {"version": draft.version, "reason": "x", "reason_code": "boshqa", "note": "x"})
        assert response.status_code == 403, key
    draft.refresh_from_db()
    assert draft.status == DutyDay.Status.DRAFT
    assert DutyDay.objects.get(date=SUNDAY).status == DutyDay.Status.APPROVED
    assert Absence.objects.filter(pk=world["absence"].pk).exists()


def test_cadet_cannot_read_other_cadets_by_typing_ids(client, world):
    client.force_login(world["cadet"])
    for pk in Cadet.objects.exclude(pk=world["me"].pk).values_list("pk", flat=True)[:30]:
        assert client.get(reverse("cadet_detail", args=[pk])).status_code == 403
    assert client.get(reverse("cadet_detail", args=[99999])).status_code == 404


def test_cadet_and_anonymous_cannot_enter_admin_panel(client, world):
    assert client.get("/admin/").status_code == 302
    client.force_login(world["cadet"])
    response = client.get("/admin/naryad/cadet/")
    assert response.status_code == 302 and "/admin/login/" in response["Location"]


def test_admin_opens_every_page(client, world):
    client.force_login(world["admin"])
    for key, url in urls(world).items():
        if key in POST_ONLY:
            continue
        expected = (403,) if key == "my_card" else (200, 302)  # “Mening tarixim” — faqat kursant roli
        assert client.get(url).status_code in expected, (key, url)


# ---------------------------------------------------------------------------
# Sarlavhalar, /health/, xato sahifalari
# ---------------------------------------------------------------------------


def test_security_headers_on_html(client, world):
    response = client.get(reverse("login"))
    csp = response["Content-Security-Policy"]
    assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp and "object-src 'none'" in csp
    assert "'unsafe-eval'" not in csp and "script-src 'self' 'unsafe-inline'" not in csp
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert response["Referrer-Policy"] == "same-origin"
    assert "httponly" in str(client.cookies.get("csrftoken", "")).lower() or response.cookies["csrftoken"]["httponly"]


def test_no_inline_javascript_in_templates():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "templates"
    for path in root.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        assert "<script>" not in text, path
        for attr in ("onclick=", "onsubmit=", "onchange=", "onload=", "javascript:"):
            assert attr not in text, (path, attr)


def test_health_endpoint(client, db, settings):
    settings.ALLOWED_HOSTS = ["naryad.example.uz"]
    response = client.get("/health/", HTTP_HOST="127.0.0.1:8000")  # konteyner ichidan, Host tekshirilmaydi
    assert response.status_code == 200 and response.json() == {"status": "ok", "database": "ok"}


def test_health_reports_database_failure(client, db, monkeypatch):
    from naryad import security

    class Broken:
        def cursor(self):
            raise RuntimeError("baza yo'q")

    monkeypatch.setattr(security, "connection", Broken())
    response = client.get("/health/")
    assert response.status_code == 503 and response.json()["status"] == "xato"


def test_uzbek_404_page(client, world):
    client.force_login(world["admin"])
    response = client.get("/mavjud-emas/")
    assert response.status_code == 404
    html = response.content.decode()
    assert "Sahifa topilmadi" in html and "Bosh sahifaga" in html


def test_uzbek_403_page(client, world):
    client.force_login(world["cadet"])
    html = client.get(reverse("stats")).content.decode()
    assert "Ruxsat yo‘q" in html


def test_uzbek_500_page_renders_without_request_context():
    from django.template.loader import render_to_string

    html = render_to_string("500.html")
    assert "Serverda xatolik" in html and "/static/css/app.css" in html


def test_prod_settings_are_strict(monkeypatch):
    import importlib
    import sys

    monkeypatch.setenv("DJANGO_SECRET_KEY", "x" * 10 + "abcdefghij" * 5)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "naryad.example.uz")
    monkeypatch.setenv("DJANGO_DEBUG", "True")  # baribir o'chadi
    original = sys.modules.get("config.settings")
    sys.modules.pop("config.settings", None)
    sys.modules.pop("config.settings_prod", None)
    try:
        prod = importlib.import_module("config.settings_prod")
    finally:
        sys.modules["config.settings"] = original
    assert prod.DEBUG is False and prod.SECURE_SSL_REDIRECT and prod.SESSION_COOKIE_SECURE and prod.CSRF_COOKIE_SECURE
    assert prod.SECURE_HSTS_SECONDS >= 31536000 and prod.X_FRAME_OPTIONS == "DENY"

    from django.core.exceptions import ImproperlyConfigured

    monkeypatch.setenv("DJANGO_SECRET_KEY", "qisqa")
    sys.modules.pop("config.settings", None)
    sys.modules.pop("config.settings_prod", None)
    try:
        with pytest.raises(ImproperlyConfigured):
            importlib.import_module("config.settings_prod")
    finally:
        sys.modules["config.settings"] = original
        sys.modules.pop("config.settings_prod", None)


# ---------------------------------------------------------------------------
# Excel yuklash cheklovlari
# ---------------------------------------------------------------------------


def xlsx_bytes(rows) -> bytes:
    wb = Workbook()
    for r in rows:
        wb.active.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_upload_rejects_wrong_type_and_size(client, world):
    from django.core.files.uploadedfile import SimpleUploadedFile

    client.force_login(world["admin"])
    url = reverse("cadet_import")
    fake = SimpleUploadedFile("kursantlar.xlsx", b"bu excel emas", content_type="application/vnd.ms-excel")
    response = client.post(url, {"file": fake}, follow=True)
    assert "formatida emas" in response.content.decode()

    csv = SimpleUploadedFile("kursantlar.csv", b"a,b", content_type="text/csv")
    assert "Faqat .xlsx" in client.post(url, {"file": csv}, follow=True).content.decode()

    big = SimpleUploadedFile("katta.xlsx", b"PK\x03\x04" + b"0" * (2 * 1024 * 1024 + 10))
    assert "juda katta" in client.post(url, {"file": big}, follow=True).content.decode()


def test_xlsx_row_limit_and_zip_checks():
    header = [["Familiya", "Ism", "Otasining ismi", "Guruh", "Jins"]]
    with pytest.raises(cadet_import.ImportFileError, match="juda ko‘p"):
        cadet_import.read_xlsx(xlsx_bytes(header + [["A", "B", "C", "BI-225", "O‘g‘il"]] * (cadet_import.MAX_ROWS + 5)))
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("hello.txt", "salom")
    with pytest.raises(cadet_import.ImportFileError, match="formatida emas"):
        cadet_import.read_xlsx(buf.getvalue())


def test_timezone_is_tashkent():
    assert str(timezone.get_default_timezone()) == "Asia/Tashkent"
