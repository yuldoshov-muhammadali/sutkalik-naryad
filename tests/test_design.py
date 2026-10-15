"""12-bosqich: institut rasmi, emblema, jonli bosh sahifa, tungi rejim (v1.3.0)."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from django.urls import reverse
from PIL import Image

from naryad.dashboard import clock_context
from naryad.models import User

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "static" / "img"
PASSWORD = "Kuchli-parol-2026"
TASHKENT = ZoneInfo("Asia/Tashkent")

EXPECTED_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; "
    "connect-src 'self'; frame-src 'self'; frame-ancestors 'none'; form-action 'self'; base-uri 'self'; object-src 'none'"
)


@pytest.fixture
def admin_client(client, db_cadets):
    client.force_login(User.objects.create_user("kursboshligi", password=PASSWORD, role="admin"))
    return client


@pytest.fixture
def cadet_client(client, db_cadets):
    from naryad.models import Cadet

    client.force_login(User.objects.create_user("kursant", password=PASSWORD, role="cadet", cadet=Cadet.objects.first()))
    return client


# ---------------------------------------------------------------------------
# Statik fayllar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["institut-1920.webp", "institut-1920.jpg", "institut-960.webp", "institut-960.jpg"])
def test_institut_images_exist_within_limit(name):
    path = IMG / name
    assert path.exists() and path.stat().st_size <= 300 * 1024
    width = Image.open(path).size[0]
    assert width == int(name.split("-")[1].split(".")[0])


def test_emblem_is_transparent_and_sized():
    for size in (512, 192, 64):
        img = Image.open(IMG / f"emblema-{size}.png")
        assert img.size == (size, size) and img.mode == "RGBA"
        assert img.getpixel((0, 0))[3] == 0  # burchak — shaffof (qora fon olib tashlangan)
        assert img.getpixel((size // 2, size // 2))[3] == 255  # markaz — to'liq ko'rinadi
    assert (IMG / "emblema.png").exists() and (IMG / "favicon.ico").exists()
    touch = Image.open(IMG / "apple-touch-icon.png")
    assert touch.size == (180, 180)
    assert (ROOT / "assets" / "institut.jpg").exists() and (ROOT / "assets" / "emblema.jpg").exists()


def test_prepare_images_is_deterministic():
    def digest():
        return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(IMG.iterdir())}

    before = digest()
    spec = importlib.util.spec_from_file_location("prepare_images", ROOT / "scripts" / "prepare_images.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
    assert digest() == before


def test_tailwind_brand_colors_and_dark_mode():
    config = (ROOT / "tailwind.config.js").read_text()
    assert 'darkMode: "class"' in config and "brand:" in config and "gold:" in config
    css = (ROOT / "static" / "css" / "app.css").read_text()
    assert ".bg-brand-900" in css and ".dark .bg-white" in css and ".text-gold-200" in css


# ---------------------------------------------------------------------------
# Sahifalar
# ---------------------------------------------------------------------------


def test_login_has_emblem_and_background(client, db):
    html = client.get(reverse("login")).content.decode()
    assert 'data-testid="login-emblem"' in html and "img/emblema-192" in html
    assert "img/institut-960.webp" in html and "img/institut-1920.webp" in html and "img/institut-1920.jpg" in html
    assert "img/favicon.ico" in html and "apple-touch-icon" in html


def test_head_loads_theme_script_before_css_and_has_toggle(client, db):
    html = client.get(reverse("login")).content.decode()
    head = html.split("</head>")[0]
    assert head.index("js/theme.js") < head.index("css/app.css")
    assert "js/theme.js\" defer" not in head  # sinxron — oq “yaltirash” bo'lmasin
    assert "data-theme-toggle" in html
    assert "<script>" not in html


@pytest.mark.parametrize("who", ["admin_client", "cadet_client"])
def test_home_hero_with_emblem_image_and_live_clock(request, who):
    client = request.getfixturevalue(who)
    response = client.get(reverse("home"))
    html = response.content.decode()
    assert 'data-testid="hero"' in html and 'data-testid="hero-emblem"' in html and 'data-testid="institut-img"' in html
    assert "960w" in html and "1920w" in html
    server_now = int(re.search(r'data-server-now="(\d+)"', html).group(1))
    assert abs(server_now / 1000 - dt.datetime.now().timestamp()) < 60
    assert "Joriy sutka:" in html and "Smena almashishiga" in html
    assert f'hx-get="{reverse("home_status")}"' in html and "data-live-status" in html
    assert "bg-white/85" in html and "backdrop-blur" in html
    assert "<script>" not in html
    assert response["Content-Security-Policy"] == EXPECTED_CSP


def test_home_status_partial_for_admin(admin_client):
    html = admin_client.get(reverse("home_status"), HTTP_HX_REQUEST="true").content.decode()
    assert "Keyingi qadam" in html and "2-kurs haftasi" in html
    assert "<html" not in html and 'data-testid="hero"' not in html


def test_home_status_partial_for_cadet(cadet_client):
    html = cadet_client.get(reverse("home_status"), HTTP_HX_REQUEST="true").content.decode()
    assert "Mening navbatdagi naryadim" in html and "Keyingi qadam" not in html and "<html" not in html


def test_home_status_not_for_anonymous(client, db):
    response = client.get(reverse("home_status"), HTTP_HX_REQUEST="true")
    assert response.status_code == 302 and response["Location"].startswith(reverse("login"))


def test_csp_unchanged(client, db):
    assert client.get(reverse("login"))["Content-Security-Policy"] == EXPECTED_CSP


# ---------------------------------------------------------------------------
# Joriy sutka hisobi (server tomoni; JS xuddi shu qoidani har soniyada takrorlaydi)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "local, label, left, pct",
    [
        (dt.datetime(2026, 10, 13, 21, 0), "13-oktabr 18:00 → 14-oktabr 18:00", "21 soat 0 daqiqa", 12.5),
        (dt.datetime(2026, 10, 14, 17, 30), "13-oktabr 18:00 → 14-oktabr 18:00", "30 daqiqa", 97.9),
        (dt.datetime(2026, 10, 14, 18, 0), "14-oktabr 18:00 → 15-oktabr 18:00", "24 soat 0 daqiqa", 0.0),
        (dt.datetime(2026, 12, 31, 23, 59, 59), "31-dekabr 18:00 → 1-yanvar 18:00", "18 soat 0 daqiqa", 25.0),
    ],
)
def test_clock_context(local, label, left, pct):
    ctx = clock_context(local.replace(tzinfo=TASHKENT))
    assert ctx["duty_label"] == label
    assert ctx["duty_left"] == f"Smena almashishiga {left} qoldi"
    assert ctx["duty_pct"] == pct
    assert ctx["time"] == local.strftime("%H:%M:%S")


def test_clock_date_in_uzbek():
    ctx = clock_context(dt.datetime(2026, 10, 14, 9, 5, 7, tzinfo=TASHKENT))
    assert ctx["date"] == "Chorshanba, 14-oktabr 2026" and ctx["time"] == "09:05:07"
