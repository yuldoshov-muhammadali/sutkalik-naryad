"""18-bosqich (v1.9) skrinshotlari: E-NARYAD nomi (bosh sahifa telefon kunduzgi/tungi, kirish sahifasi),
hujjatli Kasallar ro'yxati, rasm yuklash formasi, kursantning o'z hujjatlari. Natija: docs/skrinshotlar/v1.9/.

    BASE=http://127.0.0.1:8136 python scripts/screenshots_v19.py docs/skrinshotlar/v1.9
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8136")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
PHONE = {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
PC = {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1}


def context(browser, device, scheme="light"):
    return browser.new_context(locale="uz-UZ", color_scheme=scheme, **device)


def login(page, user):
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("form:has(#id_password) button[type=submit]")
    page.wait_for_url(BASE + "/")


with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    for scheme, suffix in (("light", "kunduzgi"), ("dark", "tungi")):
        page = context(b, PHONE, scheme).new_page()
        page.goto(BASE + "/kirish/")
        page.screenshot(path=f"{OUT}/kirish-telefon-{suffix}.png", full_page=True)
        login(page, "kursboshligi")
        page.wait_for_timeout(800)
        page.screenshot(path=f"{OUT}/bosh-sahifa-admin-telefon-{suffix}.png")
        page.context.close()
        page = context(b, PHONE, scheme).new_page()
        login(page, "kursant")
        page.wait_for_timeout(800)
        page.screenshot(path=f"{OUT}/bosh-sahifa-kursant-telefon-{suffix}.png", full_page=True)
        page.context.close()

    page = context(b, PC).new_page()
    page.goto(BASE + "/kirish/")
    page.screenshot(path=f"{OUT}/kirish-kompyuter.png")
    login(page, "kursboshligi")
    page.goto(BASE + "/kasallar/")
    page.screenshot(path=f"{OUT}/kasallar-royxati-hujjatlar-kompyuter.png", full_page=True)
    page.click("[data-testid^=docs-]")
    page.wait_for_load_state()
    page.locator("#hujjatlar").screenshot(path=f"{OUT}/hujjatlar-yuklash-kompyuter.png")
    page.context.close()

    page = context(b, PHONE).new_page()
    login(page, "kursboshligi")
    page.goto(BASE + "/kasallar/")
    href = page.locator("[data-testid^=docs-]").first.get_attribute("href")
    page.goto(BASE + href)
    page.locator("#hujjatlar").screenshot(path=f"{OUT}/hujjatlar-yuklash-telefon.png")
    page.context.close()

    page = context(b, PHONE).new_page()
    login(page, "kursant")
    page.goto(BASE + "/mening-tarixim/#hujjatlar")
    page.locator("[data-testid=my-documents]").screenshot(path=f"{OUT}/kursant-oz-hujjatlari-telefon.png")
    page.locator("[data-testid=doc-gallery] a[href^='#doc-']").first.click()
    page.wait_for_timeout(800)
    page.screenshot(path=f"{OUT}/kursant-hujjat-katta-telefon.png")
    page.context.close()
    b.close()
print("ok")
