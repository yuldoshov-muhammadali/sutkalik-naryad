"""12-bosqich (v1.3) skrinshotlari: kirish, bosh sahifa (admin, kursant), sutka sahifasi —
telefon (360 px) va kompyuter (1280 px), kunduzgi va tungi rejimda. Natija: docs/skrinshotlar/v1.3/.

    BASE=http://127.0.0.1:8125 DAY=2026-10-14 python scripts/screenshots_v13.py docs/skrinshotlar/v1.3
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8125")
DAY = os.environ.get("DAY", "2026-10-14")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
DEVICES = {
    "telefon": {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True},
    "kompyuter": {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1},
}


def context(browser, device, theme):
    ctx = browser.new_context(locale="uz-UZ", ignore_https_errors=True, **DEVICES[device])
    # Rejim tanlovi sahifa skriptlaridan oldin (Playwright init script — sahifa CSP'siga ta'sir qilmaydi)
    ctx.add_init_script(f"try {{ localStorage.setItem('naryad-theme', '{theme}'); }} catch (e) {{}}")
    return ctx


def login(page, user):
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("form:has(#id_password) button[type=submit]")
    page.wait_for_url(BASE + "/")


with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    for theme, label in (("light", "kunduzgi"), ("dark", "tungi")):
        for device in DEVICES:
            page = context(b, device, theme).new_page()
            page.goto(BASE + "/kirish/")
            page.wait_for_timeout(300)
            page.screenshot(path=f"{OUT}/kirish-{device}-{label}.png")
            login(page, "kursboshligi")
            page.wait_for_timeout(1200)
            page.screenshot(path=f"{OUT}/bosh-sahifa-admin-{device}-{label}.png", full_page=True)
            page.goto(f"{BASE}/sutka/{DAY}/")
            page.screenshot(path=f"{OUT}/sutka-{device}-{label}.png", full_page=device == "kompyuter")
            page = context(b, device, theme).new_page()
            login(page, "kursant")
            page.wait_for_timeout(1200)
            page.screenshot(path=f"{OUT}/bosh-sahifa-kursant-{device}-{label}.png", full_page=True)
    b.close()
print("ok")
