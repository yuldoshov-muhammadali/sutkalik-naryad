"""19-bosqich (v1.10) skrinshotlari: komandirning “Mening guruhim” sahifasi va bosh sahifasi (telefon), haftalik ko‘rinish,
komandir menyusi, admin panelida akkaunt yaratish formasi (rol tanlash). Natija: docs/skrinshotlar/v1.10/.

    BASE=http://127.0.0.1:8138 python scripts/screenshots_v20.py docs/skrinshotlar/v1.10
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8138")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
PHONE = {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
PC = {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1}


def login(browser, user, device, scheme="light"):
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
        page = login(b, "komandir.bi525", PHONE, scheme)
        page.goto(BASE + "/mening-guruhim/")
        page.screenshot(path=f"{OUT}/mening-guruhim-telefon-{suffix}.png", full_page=True)
        page.context.close()
    page = login(b, "komandir.bi525", PHONE)
    page.wait_for_timeout(800)
    page.screenshot(path=f"{OUT}/komandir-bosh-sahifa-telefon.png", full_page=True)
    page.click("summary[aria-label]")
    page.wait_for_timeout(300)
    page.screenshot(path=f"{OUT}/komandir-menyusi-telefon.png")
    page.goto(BASE + "/mening-guruhim/hafta/")
    page.screenshot(path=f"{OUT}/haftalik-korinish-telefon.png", full_page=True)
    page.context.close()
    page = login(b, "komandir.bi525", PC)
    page.goto(BASE + "/mening-guruhim/hafta/")
    page.screenshot(path=f"{OUT}/haftalik-korinish-kompyuter.png", full_page=True)
    page.context.close()
    page = login(b, "kursboshligi", PC)
    page.goto(BASE + "/admin/naryad/user/add/")
    page.select_option("#id_role", "commander")
    page.screenshot(path=f"{OUT}/admin-akkaunt-yaratish-rol.png", full_page=True)
    page.context.close()
    b.close()
print("ok")
