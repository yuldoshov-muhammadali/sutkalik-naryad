"""Skrinshotlar: docs/skrinshotlar/ (telefon 390 px va kompyuter 1280 px).

Ishga tushirish: server ishlab turganida (runserver 127.0.0.1:8123) va demo foydalanuvchilar
(kursboshligi / kursant, parol Demo-parol-2026) bo'lganda:
    pip install playwright && python -m playwright install chromium
    python scripts/screenshots.py docs/skrinshotlar
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = "http://127.0.0.1:8123"
PASSWORD = "Demo-parol-2026"
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
DESKTOP = {"viewport": {"width": 1280, "height": 900}, "device_scale_factor": 1}


def login(browser, user, device):
    ctx = browser.new_context(locale="uz-UZ", **device)
    page = ctx.new_page()
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_url(BASE + "/")
    return page


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    page = b.new_context(locale="uz-UZ", **PHONE).new_page()
    page.goto(BASE + "/kirish/")
    page.screenshot(path=f"{OUT}/01-login.png", full_page=True)

    page = login(b, "kursboshligi", PHONE)
    page.screenshot(path=f"{OUT}/02-bosh-sahifa-admin.png", full_page=True)
    page.click("summary")
    page.screenshot(path=f"{OUT}/04-menyu-admin.png")
    page.goto(BASE + "/kursantlar/")
    page.screenshot(path=f"{OUT}/05-kursantlar-telefon.png", full_page=False)
    page.fill("#q", "sa")
    page.wait_for_timeout(800)
    page.screenshot(path=f"{OUT}/06-kursantlar-qidiruv-telefon.png", full_page=False)

    page = login(b, "kursboshligi", DESKTOP)
    page.goto(BASE + "/kursantlar/")
    page.screenshot(path=f"{OUT}/07-kursantlar-kompyuter.png", full_page=False)
    page.goto(BASE + "/kursantlar/")
    page.click("text=Sa’dullayev Behro‘z Bahodir o‘g‘li")
    page.screenshot(path=f"{OUT}/08-kursant-kartochkasi-kompyuter.png", full_page=True)

    # 7-bosqich: sutka sahifasi (qoralama, ogohlantirish), almashtirish oynasi, haftalar
    day = os.environ.get("DAY", "2026-10-13")
    page = login(b, "kursboshligi", PHONE)
    page.goto(f"{BASE}/sutka/{day}/")
    page.screenshot(path=f"{OUT}/10-sutka-telefon.png", full_page=True)
    page.locator("button", has_text="Almashtirish").first.click()
    page.wait_for_selector("#replace-title")
    page.screenshot(path=f"{OUT}/11-almashtirish-oynasi-telefon.png")
    page = login(b, "kursboshligi", DESKTOP)
    page.goto(f"{BASE}/sutka/{day}/")
    page.screenshot(path=f"{OUT}/12-sutka-kompyuter.png", full_page=True)
    page.goto(f"{BASE}/haftalar/")
    page.screenshot(path=f"{OUT}/13-haftalar-kompyuter.png", full_page=False)

    page = login(b, "kursant", PHONE)
    page.screenshot(path=f"{OUT}/03-bosh-sahifa-kursant.png", full_page=True)
    page.goto(BASE + "/mening-tarixim/")
    page.screenshot(path=f"{OUT}/09-mening-tarixim-telefon.png", full_page=True)
    b.close()
print("ok")
