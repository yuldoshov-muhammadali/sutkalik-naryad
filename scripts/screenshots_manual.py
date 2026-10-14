"""Qo'llanma skrinshotlari va production'dagi to'liq oqim sinovi (10-bosqich).

Bo'sh (faqat load_roster va boshlang'ich taqsimot kiritilgan) production serverida brauzer orqali:
hafta ochish → sutkani tuzish → almashtirish (sabab bilan) → tasdiqlash → PDF → sababli holat →
statistika, so'ng kursant sifatida kirish. Har qadamda skrinshot: docs/qollanma/rasmlar/.

    BASE=https://naryad.example.uz python scripts/screenshots_manual.py docs/qollanma/rasmlar
"""

from __future__ import annotations

import datetime as dt
import os
import sys

from playwright.sync_api import expect, sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "https://localhost")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
DAY = dt.date.fromisoformat(os.environ.get("DAY", "2026-10-13"))
SUNDAY = DAY - dt.timedelta(days=(DAY.weekday() + 1) % 7)
PHONE = {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
DESKTOP = {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1}


def context(browser, device):
    return browser.new_context(locale="uz-UZ", ignore_https_errors=True, accept_downloads=True, **device)


def login(page, user):
    page.goto(BASE + "/kirish/")
    page.fill("#id_username", user)
    page.fill("#id_password", PASSWORD)
    page.click("button[type=submit]")
    page.wait_for_url(BASE + "/")


def shot(page, name, full=False):
    page.screenshot(path=f"{OUT}/{name}.png", full_page=full)
    print("rasm:", name)


with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)

    # --- Admin, kompyuter ---
    page = context(b, PHONE).new_page()
    page.goto(BASE + "/kirish/")
    shot(page, "01-kirish-telefon")

    page = context(b, DESKTOP).new_page()
    login(page, "kursboshligi")
    shot(page, "02-bosh-sahifa-admin")

    page.goto(BASE + "/haftalar/")
    page.fill("input[name=start_date]", SUNDAY.isoformat())
    page.locator("input[name=start_date]").dispatch_event("change")
    page.wait_for_timeout(600)
    shot(page, "03-hafta-ochish")
    page.click("button:has-text('Haftani ochish')")
    page.wait_for_load_state()
    expect(page.locator("body")).to_contain_text("ochildi")

    page.goto(f"{BASE}/sutka/{DAY.isoformat()}/")
    shot(page, "04-sutka-tuzilmagan")
    page.click("button:has-text('Tuzish')")
    page.wait_for_load_state()
    expect(page.locator("body")).to_contain_text("Qoralama")
    shot(page, "05-qoralama", full=True)

    page.locator("button", has_text="Almashtirish").first.click()
    page.wait_for_selector("#replace-title")
    page.select_option("select[name=reason]", "kasal")
    shot(page, "06-almashtirish-oynasi")
    page.click("#modal button:has-text('Saqlash')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    shot(page, "07-almashtirilgan")

    page.click("button:has-text('Tasdiqlash')")
    page.wait_for_load_state()
    expect(page.locator("body")).to_contain_text("Tasdiqlangan")
    shot(page, "08-tasdiqlangan", full=True)

    with page.expect_download() as dl:
        page.click("text=PDF yuklab olish")
    pdf_path = f"{OUT}/../namuna-{DAY.isoformat()}.pdf"
    dl.value.save_as(pdf_path)
    print("pdf:", dl.value.suggested_filename, os.path.getsize(pdf_path), "bayt")

    page.goto(f"{BASE}/sutka/{DAY.isoformat()}/jurnal/")
    shot(page, "09-jurnal")

    page.goto(BASE + "/sababli/")
    shot(page, "10-sababli-holatlar", full=True)

    page.goto(BASE + "/kursantlar/")
    shot(page, "11-kursantlar")
    page.goto(BASE + "/statistika/")
    shot(page, "12-statistika")
    page.goto(BASE + "/")
    shot(page, "13-bosh-sahifa-tasdiqdan-keyin", full=True)

    # --- Admin, telefon ---
    page = context(b, PHONE).new_page()
    login(page, "kursboshligi")
    page.goto(f"{BASE}/sutka/{DAY.isoformat()}/")
    shot(page, "14-sutka-telefon")
    page.click("summary:has-text('Menyu')")
    shot(page, "15-menyu-telefon")

    # --- Kursant, telefon ---
    page = context(b, PHONE).new_page()
    login(page, "kursant")
    shot(page, "16-kursant-bosh-sahifa", full=True)
    page.goto(BASE + "/mening-tarixim/")
    shot(page, "17-kursant-mening-tarixim", full=True)
    page.goto(BASE + "/sutkalar/")
    shot(page, "18-kursant-tasdiqlangan-naryadlar")
    page.goto(f"{BASE}/sutka/{DAY.isoformat()}/")
    shot(page, "19-kursant-sutka")
    page.goto(BASE + "/parol/")
    shot(page, "20-parol-almashtirish")
    page.goto(BASE + "/statistika/")
    shot(page, "21-kursantga-ruxsat-yoq")
    b.close()
print("ok")
