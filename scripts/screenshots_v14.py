"""13-bosqich (v1.4) skrinshotlari: bosh sahifa uch tilda (o'zbek, rus, ingliz) — telefon (360 px) va kompyuter
(1280 px). Til kirish sahifasidagi UZ | RU | EN tugmasi bilan tanlanadi. Natija: docs/skrinshotlar/v1.4/.

    BASE=http://127.0.0.1:8126 python scripts/screenshots_v14.py docs/skrinshotlar/v1.4
"""
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
BASE = os.environ.get("BASE", "http://127.0.0.1:8126")
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
DEVICES = {
    "telefon": {"viewport": {"width": 360, "height": 780}, "device_scale_factor": 2, "is_mobile": True, "has_touch": True},
    "kompyuter": {"viewport": {"width": 1280, "height": 860}, "device_scale_factor": 1},
}

with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    for lang in ("uz", "ru", "en"):
        for device, options in DEVICES.items():
            # brauzer tili ruscha bo'lsa ham platforma o'zbekcha ochiladi — tilni faqat tugma o'zgartiradi
            page = b.new_context(locale="ru-RU", ignore_https_errors=True, **options).new_page()
            page.goto(BASE + "/kirish/")
            page.click(f"[data-testid=language-switch] button[value={lang}]")
            page.wait_for_load_state()
            if device == "telefon":
                page.screenshot(path=f"{OUT}/kirish-{lang}-{device}.png")
            page.fill("#id_username", "kursboshligi")
            page.fill("#id_password", PASSWORD)
            page.click("form:has(#id_password) button[type=submit]")
            page.wait_for_url(BASE + "/")
            page.wait_for_timeout(1200)
            assert page.get_attribute("html", "lang") == lang
            page.screenshot(path=f"{OUT}/bosh-sahifa-{lang}-{device}.png", full_page=device == "telefon")
            page.context.close()
    b.close()
print("ok")
