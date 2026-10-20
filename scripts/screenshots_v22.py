"""21-bosqich (v1.12) skrinshotlari: kursantlar ro'yxatida faqat lavozim nomi, Sozlamalardagi yangi bo'lim, sutka sahifasidagi
tushuntirish jadvali va ogohlantirish, almashtirish oynasida “dam olmagan” kursant (qizil ogohlantirish va sabab),
statistikadagi “Og‘ir joylar” ustuni, kursant kartochkasidagi tsikl. Natija: docs/skrinshotlar/v1.12/.

Demo baza: simulate_weeks.py --komandirlar, keyin QOIDA A ogohlantirishi chiqqan sutka qoralama holida qoldiriladi.

    BASE=http://127.0.0.1:8140 DAY=2026-11-21 CADET=3 python scripts/screenshots_v22.py docs/skrinshotlar/v1.12
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8140")
DAY = os.environ["DAY"]
CADET = os.environ["CADET"]
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
PHONE = {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True}
PC = {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1}


def login(browser, user, device):
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
    page = login(b, "kursboshligi", PC)

    page.goto(BASE + "/kursantlar/?holat=lavozimda")
    page.locator("#results").screenshot(path=f"{OUT}/kursantlar-faqat-lavozim.png")
    page.goto(BASE + "/admin/naryad/cadet/?lavozim=komandir")
    page.screenshot(path=f"{OUT}/admin-lavozim-filtri.png", full_page=True)

    page.goto(BASE + "/admin/naryad/setting/1/change/")
    page.locator("fieldset:has-text('og‘ir joylar')").first.screenshot(path=f"{OUT}/sozlamalar-joylar-navbati.png")

    page.goto(BASE + f"/sutka/{DAY}/")
    page.click("[data-testid=explanations] summary")
    page.locator("[data-testid=rotation-notices]").screenshot(path=f"{OUT}/sutka-ogohlantirish-qoida-a.png")
    page.locator("[data-testid=explanations]").screenshot(path=f"{OUT}/sutka-tushuntirish-jadvali.png")

    # Almashtirish oynasi: 1-NO‘J oxirgi posbon o'rni, kecha turgan (dam olmagan) kursant tanlanadi
    page.locator("li:has-text('1-NO‘J bo‘yicha posbon') button:has-text('Almashtirish')").last.click()
    page.wait_for_selector("[data-testid=no-rest-candidate]")
    page.locator("label:has([data-testid=no-rest-candidate]) input[type=radio]").first.check()
    page.fill("textarea[name=no_rest_reason]", "Guruhda kasallar ko‘p, boshqa kishi qolmadi")
    page.check("input[name=no_rest_confirm]")
    page.select_option("select[name=reason]", "sababli")
    page.locator("#modal [role=dialog] > div").screenshot(path=f"{OUT}/almashtirish-dam-olmagan.png")
    page.click("#modal button[type=submit]")
    page.wait_for_selector("[data-testid=no-rest-badge]")
    page.screenshot(path=f"{OUT}/sutka-dam-olmagan-belgisi.png", full_page=True)

    page.goto(BASE + "/statistika/?guruh=YuP-125")
    page.locator("[data-testid=boys-table]").screenshot(path=f"{OUT}/statistika-ogir-joylar.png")
    page.locator("section[aria-labelledby=fair-title]").screenshot(path=f"{OUT}/statistika-adolat-ogir-farq.png")

    page.goto(BASE + f"/kursantlar/{CADET}/")
    page.locator("[data-testid=post-rotation]").screenshot(path=f"{OUT}/kartochka-tsikl.png")
    page.context.close()

    page = login(b, "kursboshligi", PHONE)
    page.goto(BASE + f"/sutka/{DAY}/")
    page.screenshot(path=f"{OUT}/sutka-telefon.png", full_page=True)
    page.context.close()
    b.close()
print("ok")
