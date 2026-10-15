"""15-bosqich (v1.6) skrinshotlari: Zalyotchiklar sahifasi, sutkadagi jazo o'rni, kursant kartochkasi (admin)
va kursant bosh sahifasi (navbatdan tashqari naryad). Natija: docs/skrinshotlar/v1.6/.

    BASE=http://127.0.0.1:8128 DAY=2026-10-17 CADET_ID=12 python scripts/screenshots_v16.py docs/skrinshotlar/v1.6
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8128")
DAY = os.environ.get("DAY", "2026-10-17")
CADET_ID = os.environ.get("CADET_ID", "1")
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
    for device, label in ((PHONE, "telefon"), (PC, "kompyuter")):
        page = page_for(b, "kursboshligi", device)
        page.goto(BASE + "/zalyotchiklar/")
        page.screenshot(path=f"{OUT}/zalyotchiklar-{label}.png", full_page=True)
        page.goto(f"{BASE}/sutka/{DAY}/")
        # 1-NO‘J va 1-Yotoqxona bo'limlari (jazo o'rinlari “Zalyot” belgisi bilan) — sahifa koordinatalarida
        top, bottom = page.evaluate("""() => {
            const rows = [...document.querySelectorAll('[data-testid=penalty-row]')].map(r => r.closest('ul') || r);
            const rects = rows.map(r => r.getBoundingClientRect());
            return [Math.min(...rects.map(r => r.top)) + window.scrollY - 70, Math.max(...rects.map(r => r.bottom)) + window.scrollY + 16];
        }""")
        page.screenshot(path=f"{OUT}/sutka-jazo-orni-{label}.png", full_page=True,
                        clip={"x": 0, "y": max(0, top), "width": device["viewport"]["width"], "height": bottom - max(0, top)})
        page.goto(f"{BASE}/kursantlar/{CADET_ID}/")
        page.screenshot(path=f"{OUT}/kursant-kartochkasi-admin-{label}.png", full_page=True)
        page.context.close()
    page = page_for(b, "kursant", PHONE)
    page.wait_for_timeout(1200)
    page.screenshot(path=f"{OUT}/kursant-bosh-sahifa-telefon.png", full_page=True)
    b.close()
print("ok")
