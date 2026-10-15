"""14-bosqich (v1.5) skrinshotlari: kursant bosh sahifasi (telefon, kunduzgi va tungi) va admin banneri.
Natija: docs/skrinshotlar/v1.5/.

    BASE=http://127.0.0.1:8127 python scripts/screenshots_v15.py docs/skrinshotlar/v1.5 kursant
    BASE=http://127.0.0.1:8127 python scripts/screenshots_v15.py docs/skrinshotlar/v1.5 admin sariq   # yoki yashil
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT, MODE = sys.argv[1], sys.argv[2]
LABEL = sys.argv[3] if len(sys.argv) > 3 else ""
BASE = os.environ.get("BASE", "http://127.0.0.1:8127")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
PHONE = {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}


def page_for(browser, user, theme):
    ctx = browser.new_context(locale="uz-UZ", **PHONE)
    ctx.add_init_script(f"try {{ localStorage.setItem('naryad-theme', '{theme}'); }} catch (e) {{}}")
    page = ctx.new_page()
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("form:has(#id_password) button[type=submit]")
    page.wait_for_url(BASE + "/")
    page.wait_for_timeout(1200)
    return page


with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    if MODE == "kursant":
        for theme, label in (("light", "kunduzgi"), ("dark", "tungi")):
            page = page_for(b, "kursant", theme)
            page.screenshot(path=f"{OUT}/kursant-bosh-sahifa-telefon-{label}.png", full_page=True)
            page.context.close()
    else:
        page = page_for(b, "kursboshligi", "light")
        box = page.locator("[data-testid=approval-banner]").bounding_box()
        page.screenshot(path=f"{OUT}/admin-banner-{LABEL}-telefon.png",
                        clip={"x": 0, "y": 0, "width": 360, "height": min(780, box["y"] + box["height"] + 24)})
        page.context.close()
    b.close()
print("ok")
