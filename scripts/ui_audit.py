"""Interfeys auditi (10-bosqich): har sahifani telefon (360 px) va kompyuter (1280 px) kengligida ochib tekshiradi.

- gorizontal toshish (sahifa ekrandan keng bo'lib qolmasin; jadvallar o'z qutisida aylanadi);
- 44 px dan kichik tugma, menyu havolasi, maydon;
- sarlavha (h1) bor-yo'qligi;
- inglizcha qolgan matnlar;
- Content-Security-Policy buzilishlari va JavaScript xatolari (brauzer konsoli).

Ishga tushirish (server ishlab turganida, simulyatsiya bazasi bilan — scripts/simulate_weeks.py):
    python scripts/ui_audit.py http://127.0.0.1:8123 natija_papka
"""

from __future__ import annotations

import json
import os
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8123"
OUT = sys.argv[2] if len(sys.argv) > 2 else "audit"
PASSWORD = os.environ.get("PASSWORD", "Demo-parol-2026")
DAY_APPROVED = os.environ.get("DAY_APPROVED", "2026-10-12")
DAY_DRAFT = os.environ.get("DAY_DRAFT", "2026-10-13")
CADET_ID = os.environ.get("CADET_ID", "1")

ADMIN_PAGES = [
    "/", "/haftalar/", "/sababli/", "/kursantlar/", "/kursantlar/qoshish/", "/kursantlar/import/",
    f"/kursantlar/{CADET_ID}/", f"/kursantlar/{CADET_ID}/tahrirlash/", f"/sutka/{DAY_DRAFT}/", f"/sutka/{DAY_APPROVED}/",
    f"/sutka/{DAY_APPROVED}/jurnal/", "/sutkalar/", "/statistika/", "/parol/", "/yoq-sahifa/",
    "/admin/", "/admin/naryad/cadet/", "/admin/naryad/setting/1/change/",
]
CADET_PAGES = ["/", "/mening-tarixim/", "/sutkalar/", f"/sutka/{DAY_APPROVED}/", "/parol/", "/statistika/"]
ANON_PAGES = ["/kirish/"]

AUDIT_JS = """
() => {
  const issues = [];
  const doc = document.documentElement;
  if (doc.scrollWidth > window.innerWidth + 1) issues.push(`gorizontal toshish: ${doc.scrollWidth}px > ${window.innerWidth}px`);
  if (!document.querySelector('h1')) issues.push('h1 sarlavha yo‘q');
  const sel = 'button, summary, select, input:not([type=hidden]):not([type=checkbox]):not([type=radio]), textarea, a.btn, header a, nav a, main a[class*="rounded"][class*="px-"]';
  for (const el of document.querySelectorAll(sel)) {
    const r = el.getBoundingClientRect();
    const st = getComputedStyle(el);
    if (!r.width || !r.height || st.visibility === 'hidden' || st.display === 'none') continue;
    if (el.closest('table, #changelist-filter, .paginator, .breadcrumbs, #toolbar, .object-tools, .actions, #nav-sidebar')) continue;
    if (r.height < 43.5) {
      const text = (el.innerText || el.value || el.getAttribute('aria-label') || el.name || el.tagName).trim().slice(0, 40);
      issues.push(`kichik (${Math.round(r.width)}×${Math.round(r.height)}): <${el.tagName.toLowerCase()}> ${text}`);
    }
  }
  const english = /\b(the|Add|Change|Delete|Save|Search|History|Filter|Action|selected|View site|Log out|Welcome|Recent actions|None available|Select|Show all|Clear all|Yes|Documentation|Previous|Next|Today|Now|Choose|Remove|Home)\b/;
  const m = (document.body.innerText || '').match(english);
  if (m) issues.push(`inglizcha matn: "${m[0]}"`);
  return issues;
}
"""


def login(browser, user, viewport):
    ctx = browser.new_context(locale="uz-UZ", viewport=viewport, ignore_https_errors=True)
    page = ctx.new_page()
    if user:
        page.goto(BASE + "/kirish/")
        page.fill("#id_username", user)
        page.fill("#id_password", PASSWORD)
        page.click("button[type=submit]")
        page.wait_for_load_state()
    return page


def audit(page, path, tag, report):
    console = []
    page.on("console", lambda m: console.append(m.text) if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: console.append(str(e)))
    page.goto(BASE + path)
    page.wait_for_load_state("networkidle")
    issues = page.evaluate(AUDIT_JS)
    issues += [f"konsol: {c[:160]}" for c in console if "Content Security Policy" in c or "Error" in c or "Refused" in c]
    name = f"{tag}{path.strip('/').replace('/', '_') or 'bosh'}"
    page.screenshot(path=f"{OUT}/{name}.png", full_page=True)
    report[name] = issues


with sync_playwright() as p:
    os.makedirs(OUT, exist_ok=True)
    b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
    report: dict[str, list[str]] = {}
    for width, label in [(360, "tel"), (1280, "pc")]:
        viewport = {"width": width, "height": 800}
        for user, pages in [("kursboshligi", ADMIN_PAGES), ("kursant", CADET_PAGES), (None, ANON_PAGES)]:
            page = login(b, user, viewport)
            for path in pages:
                audit(page, path, f"{label}-{user or 'anon'}-", report)
            page.context.close()
    b.close()
bad = {k: v for k, v in report.items() if v}
print(json.dumps(bad, ensure_ascii=False, indent=1))
print(f"{len(report)} ta sahifa tekshirildi, muammoli: {len(bad)}")
