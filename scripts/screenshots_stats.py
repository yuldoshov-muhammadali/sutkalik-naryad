"""9-bosqich skrinshotlari: statistika sahifasi (telefon va kompyuter), bosh sahifadagi adolat belgilari,
kursant kartochkasidagi solishtirish.

Avval alohida bazada simulyatsiya (scripts/simulate_weeks.py), so'ng shu baza bilan runserver 127.0.0.1:8123:
    python scripts/screenshots_stats.py docs/skrinshotlar
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = "http://127.0.0.1:8123"
PASSWORD = "Demo-parol-2026"
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
DESKTOP = {"viewport": {"width": 1280, "height": 900}, "device_scale_factor": 1}
GROUP = os.environ.get("GROUP", "BI-325")


def login(browser, user, device):
    page = browser.new_context(locale="uz-UZ", **device).new_page()
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("form:has(#id_password) button[type=submit]")
    page.wait_for_url(BASE + "/")
    return page


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)

    page = login(b, "kursboshligi", DESKTOP)
    page.screenshot(path=f"{OUT}/14-bosh-sahifa-adolat-kompyuter.png", full_page=True)
    page.goto(f"{BASE}/statistika/?guruh={GROUP}")
    page.locator("main details").first.evaluate("e => e.open = true")
    page.screenshot(path=f"{OUT}/15-statistika-kompyuter.png", full_page=True)

    page = login(b, "kursboshligi", PHONE)
    page.goto(f"{BASE}/statistika/?guruh={GROUP}")
    page.screenshot(path=f"{OUT}/16-statistika-telefon.png", full_page=True)
    table = page.locator("[data-testid=boys-table]")
    table.scroll_into_view_if_needed()
    page.evaluate("window.scrollBy(0, -60)")
    table.evaluate("e => { e.scrollLeft = 260; e.scrollTop = 140; }")
    page.wait_for_timeout(200)
    page.screenshot(path=f"{OUT}/17-statistika-telefon-jadval-aylantirilgan.png")

    page = login(b, "kursant", PHONE)
    page.goto(BASE + "/mening-tarixim/")
    page.screenshot(path=f"{OUT}/18-kursant-solishtirish-telefon.png", full_page=False)
    b.close()
print("ok")
