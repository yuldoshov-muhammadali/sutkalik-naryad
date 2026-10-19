"""16-bosqich (v1.7) skrinshotlari: kursantning tasdiqlangan ro'yxati (telefon, eslatma bilan), tasdiqlangan
naryadlar ro'yxati, kursant bosh sahifasi va “ozod” yozuvisiz guruh jadvallari (admin). Natija: docs/skrinshotlar/v1.7/.

    BASE=http://127.0.0.1:8131 DAY=2026-10-17 python scripts/screenshots_v17.py docs/skrinshotlar/v1.7
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8131")
DAY = os.environ.get("DAY", "2026-10-17")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
PHONE = {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
PC = {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1}


def page_for(browser, user, device, scheme="light"):
    page = browser.new_context(locale="uz-UZ", color_scheme=scheme, **device).new_page()
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("form:has(#id_password) button[type=submit]")
    page.wait_for_url(BASE + "/")
    return page


with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    for scheme, suffix in (("light", "kunduzgi"), ("dark", "tungi")):
        page = page_for(b, "kursant", PHONE, scheme)
        page.goto(f"{BASE}/sutka/{DAY}/")
        page.screenshot(path=f"{OUT}/kursant-tasdiqlangan-royxat-telefon-{suffix}.png", full_page=True)
        page.context.close()
    page = page_for(b, "kursant", PHONE)
    page.goto(f"{BASE}/sutka/{DAY}/")
    page.locator("[data-testid=my-row]").scroll_into_view_if_needed()
    page.screenshot(path=f"{OUT}/kursant-oz-orni-telefon.png")
    page.goto(BASE + "/sutkalar/")
    page.screenshot(path=f"{OUT}/kursant-tasdiqlangan-naryadlar-telefon.png", full_page=True)
    page.goto(BASE + "/")
    page.wait_for_timeout(1200)
    page.screenshot(path=f"{OUT}/kursant-bosh-sahifa-telefon.png", full_page=True)
    page.context.close()

    for device, label in ((PC, "kompyuter"), (PHONE, "telefon")):
        page = page_for(b, "kursboshligi", device)
        page.goto(BASE + "/statistika/")
        # BI-525 guruh jadvali (lavozim yozuvi bilan, “ozod” yo'q)
        table = page.locator("section[aria-labelledby=boys-title]")
        table.screenshot(path=f"{OUT}/guruh-jadvali-lavozim-{label}.png")
        page.goto(BASE + "/kursantlar/")
        page.screenshot(path=f"{OUT}/kursantlar-royxati-{label}.png", full_page=True)
        page.context.close()
    b.close()
print("ok")
