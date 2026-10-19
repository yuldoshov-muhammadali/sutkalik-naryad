"""17-bosqich (v1.8) skrinshotlari: Kasallar ro'yxati, qo'shish formasi, qoralamadagi sariq ogohlantirish,
almashtirish oynasida kasal kursant va kasal kursantning bosh sahifasi (telefon). Natija: docs/skrinshotlar/v1.8/.

    BASE=http://127.0.0.1:8133 DAY=2026-10-17 python scripts/screenshots_v18.py docs/skrinshotlar/v1.8
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8133")
DAY = os.environ.get("DAY", "2026-10-17")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
PHONE = {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
PC = {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1}


def page_for(browser, user, device):
    page = browser.new_context(locale="uz-UZ", **device).new_page()
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("form:has(#id_password) button[type=submit]")
    page.wait_for_url(BASE + "/")
    return page


with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    for device, label in ((PC, "kompyuter"), (PHONE, "telefon")):
        page = page_for(b, "kursboshligi", device)
        page.goto(BASE + "/kasallar/?holat=hammasi")
        page.screenshot(path=f"{OUT}/kasallar-royxati-{label}.png", full_page=True)
        page.goto(BASE + "/kasallar/qoshish/")
        page.fill("#cadet-search", "Qodir")
        page.screenshot(path=f"{OUT}/kasallik-qoshish-{label}.png", full_page=True)
        page.goto(f"{BASE}/sutka/{DAY}/")
        page.locator("[data-testid=sick-issues]").screenshot(path=f"{OUT}/qoralamada-kasal-ogohlantirish-{label}.png")
        replace_url = page.locator("[data-testid=sick-issues] button[hx-get]").first.get_attribute("hx-get")
        page.goto(BASE + replace_url)
        # kasal kursant chetlatilganlar orasida — ro'yxat oxiriga suriladi
        page.evaluate("() => { const ul = document.querySelector('form ul'); ul.scrollTop = ul.scrollHeight; }")
        page.locator("text=Kasal:").first.scroll_into_view_if_needed()
        page.screenshot(path=f"{OUT}/almashtirishda-kasal-{label}.png", full_page=True)
        page.context.close()
    page = page_for(b, "kursant", PHONE)
    page.wait_for_timeout(1200)
    page.screenshot(path=f"{OUT}/kasal-kursant-bosh-sahifa-telefon.png", full_page=True)
    b.close()
print("ok")
