"""Namunaviy hisob: haqiqiy 100 kishilik ro'yxat bilan 19, 20 va 21-sentabr sutkalari.

Ishga tushirish (loyiha ildizidan):
    python scripts/demo.py

Tarix sifatida docs/Naryad_tartiblangan.docx dagi 18-sentabr ro'yxati olinadi
(hafta 2026-09-13 yakshanba 18:00 da boshlangan deb hisoblanadi; 13–17-sentabr
sutkalari ma'lumoti yo'q). Har tuzilgan sutka "tasdiqlangan" deb tarixga qo'shiladi.
Natija Markdown jadvallar ko'rinishida chiqariladi (docs/02-algoritm.md uchun).
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from naryad.engine import generate_day, week_start  # noqa: E402
from naryad.engine.config import POSTS, POSTS_BY_CODE, ROTATION_CHAIN  # noqa: E402
from naryad.engine.models import FEMALE, MALE, ROLE_TITLES, Cadet, DayResult, Record  # noqa: E402

ROSTER_PATH = ROOT / "data" / "roster.json"

# docs/Naryad_tartiblangan.docx — 2026-yil 18-sentabr kunidan 19-sentabr kuniga.
# Ismlar rasmiy ro'yxat bo'yicha (CLAUDE.md 10-bo'lim, 2-band): namunadagi
# "Mehmonov", "Yo‘ldoshov", "Mahmudova" — ro'yxatda "Mexmonov", "Yuldoshov", "Maxmudova".
SEPT_18 = [
    # (joy, o'rin, guruh, familiya, ism bosh harfi)
    ("markaz", 1, "BI-625", "G‘ayratov", "G‘"),
    ("noj1", 1, "BI-525", "Sa’dullayev", "B"),
    ("noj1", 2, "BI-525", "Maxsudov", "H"),
    ("noj1", 3, "BI-525", "Aslonov", "A"),
    ("noj1", 4, "BI-525", "Yuldoshov", "M"),
    ("noj2", 1, "BI-425", "G‘iyozov", "I"),
    ("noj2", 2, "BI-425", "Safarov", "M"),
    ("noj2", 3, "BI-425", "Mirzakarimov", "O"),
    ("yotoq1", 1, "BI-225", "Ozodov", "A"),
    ("yotoq1", 2, "BI-225", "Shodiyev", "R"),
    ("yotoq1", 3, "BI-225", "Umirov", "Y"),
    ("oquv", 1, "BI-325", "Xudoyberdiyev", "R"),
    ("oquv", 2, "BI-325", "Shavkatov", "Sh"),
    ("patrul", 1, "YuP-125", "Kazaxbayev", "A"),
    ("patrul", 2, "YuP-125", "Kukanov", "A"),
    ("patrul", 3, "YuP-125", "Mexmonov", "Sh"),
    ("patrul", 4, "YuP-125", "Hakimjonov", "A"),
    ("qizlar", 1, "BI-425", "Panjiyeva", "M"),
    ("qizlar", 2, "BI-325", "Zoirova", "S"),
    ("qizlar", 3, "BI-625", "Maxmudova", "H"),
]
HISTORY_DAY = dt.date(2026, 9, 18)
DEMO_DAYS = [dt.date(2026, 9, 19), dt.date(2026, 9, 20), dt.date(2026, 9, 21)]
EXPLAIN_DAY = dt.date(2026, 9, 19)
EXPLAIN_POST = "noj2"  # 19-sentabr: BI-525 kecha 1-NO‘J da edi, bugun 2-NO‘J ga o'tadi
FAIRNESS_WEEK = dt.date(2026, 9, 27)  # 7 sutkalik simulyatsiya: keyingi 2-kurs haftasi (14 kundan keyin)

UZ_MONTHS = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]
UZ_WEEKDAYS = ["dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba", "yakshanba"]


def load_roster() -> list[Cadet]:
    data = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    return [
        Cadet(
            id=c["id"],
            last_name=c["last_name"],
            first_name=c["first_name"],
            patronymic=c["patronymic"],
            group=c["group"],
            gender=c["gender"],
            short_name=c["short_name"],
        )
        for c in data
    ]


def build_history(cadets: list[Cadet]) -> list[Record]:
    records = []
    for post_code, position, group, last, initial in SEPT_18:
        matches = [c for c in cadets if c.group == group and c.short_name == f"{last} {initial}"]
        if len(matches) != 1:
            sys.exit(f"18-sentabr ro'yxatidagi kursant topilmadi yoki bir nechta: {last} {initial} ({group})")
        slot = POSTS_BY_CODE[post_code].slots[position - 1]
        records.append(Record(day=HISTORY_DAY, cadet_id=matches[0].id, post=post_code, role=slot.role, group=group, position=position))
    return records


def fmt_date(d: dt.date) -> str:
    return f"{d.day}-{UZ_MONTHS[d.month - 1]}"


def title(d: dt.date) -> str:
    nxt = d + dt.timedelta(days=1)
    return f"{d.year}-yil {fmt_date(d)} kunidan {fmt_date(nxt)} kuniga ({UZ_WEEKDAYS[d.weekday()]}, hafta {week_start(d).isoformat()} dan)"


def day_table(res: DayResult, by_id: dict[int, Cadet]) -> str:
    lines = ["| Lavozim | F.I.Sh. | Guruh |", "|---|---|---|"]
    for post in POSTS:
        if post.size > 1:
            lines.append(f"| **{post.section_title}** | | |")
        for a in [x for x in res.assignments if x.slot.post == post.code]:
            label = a.slot.pdf_label if a.slot.show_label else ""
            if a.cadet_id is None:
                lines.append(f"| {label} | — *bo‘sh* — | |")
            else:
                c = by_id[a.cadet_id]
                lines.append(f"| {label} | {c.display_name} | {c.group} |")
    return "\n".join(lines)


def explain_table(res: DayResult, post_code: str, by_id: dict[int, Cadet]) -> str:
    pick = res.picks[post_code]
    group = res.group_by_post.get(post_code, "qizlar")
    roles = {a.cadet_id: ROLE_TITLES[a.slot.role] for a in res.filled if a.slot.post == post_code}
    lines = [
        f"Guruh: **{group}**, joy: **{POSTS_BY_CODE[post_code].name}** ({POSTS_BY_CODE[post_code].size} o‘rin).",
        "",
        "| # | Kursant | Haftadagi soni | Jami | Jarima (oxirgisi shu joy) | Shu joyda | Oxirgi naryad | Tasodif (sha256) | Natija |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, s in enumerate(pick.ranking, start=1):
        c = by_id[s.cadet_id]
        result = f"✅ {roles[s.cadet_id]}" if s.cadet_id in pick.chosen else "—"
        lines.append(
            f"| {i} | {c.display_name} | {s.week_count} | {s.total} | {s.penalty} | {s.post_count} | "
            f"{s.last_day.isoformat() if s.last_day else '—'} | `{s.tiebreak[:8]}` | {result} |"
        )
    for cid, reason in pick.excluded.items():
        lines.append(f"| ✖ | {by_id[cid].display_name} | | | | | | | chiqarildi: {reason} |")
    return "\n".join(lines)


def fairness_table(cadets: list[Cadet], start: dt.date, history: list[Record]) -> tuple[str, list[DayResult]]:
    hist = list(history)
    results = []
    for i in range(7):
        res = generate_day(start + dt.timedelta(days=i), cadets, hist)
        results.append(res)
        hist.extend(res.to_records())
    counts = Counter(a.cadet_id for r in results for a in r.filled)
    pools: dict[str, list[Cadet]] = {}
    for c in cadets:
        pools.setdefault(c.group if c.gender == MALE else "Qizlar (13)", []).append(c)
    lines = [
        "| Hovuz | Kishi | Haftadagi o‘rinlar | 1 marta | 2 marta | 3+ marta | min | max | Farq (max−min) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for key in sorted(pools, key=lambda k: (k.startswith("Qizlar"), k)):
        values = [counts[c.id] for c in pools[key]]
        dist = Counter(values)
        lines.append(
            f"| {key} | {len(values)} | {sum(values)} | {dist[1]} | {dist[2]} | {sum(v for k, v in dist.items() if k >= 3)} | "
            f"{min(values)} | {max(values)} | **{max(values) - min(values)}** |"
        )
    rot = ["| Sutka | " + " | ".join(POSTS_BY_CODE[c].name for c in ROTATION_CHAIN) + " |", "|---" * 7 + "|"]
    for r in results:
        rot.append(f"| {fmt_date(r.day)} | " + " | ".join(r.group_by_post[c] for c in ROTATION_CHAIN) + " |")
    return "\n".join(lines) + "\n\nGuruhlar aylanishi:\n\n" + "\n".join(rot), results


def main() -> None:
    cadets = load_roster()
    by_id = {c.id: c for c in cadets}
    history = build_history(cadets)

    print("# Namunaviy hisob (scripts/demo.py)\n")
    print(f"Tarix: {title(HISTORY_DAY)} — docs/Naryad_tartiblangan.docx dagi ro'yxat.\n")
    print(day_table(DayResult(HISTORY_DAY, week_start(HISTORY_DAY), {}, _assignments_from(history)), by_id))

    results = []
    for day in DEMO_DAYS:
        res = generate_day(day, cadets, history)
        results.append(res)
        print(f"\n## {title(day)}\n")
        print("Guruhlar: " + ", ".join(f"{POSTS_BY_CODE[c].name} — {res.group_by_post[c]}" for c in ROTATION_CHAIN) + "\n")
        print(day_table(res, by_id))
        if res.warnings:
            print("\nOgohlantirishlar:")
            for w in res.warnings:
                print(f"- {w}")
        history.extend(res.to_records())

    explain = next(r for r in results if r.day == EXPLAIN_DAY)
    print(f"\n## Nima uchun aynan shu kursantlar: {fmt_date(EXPLAIN_DAY)}, {POSTS_BY_CODE[EXPLAIN_POST].name}\n")
    print(explain_table(explain, EXPLAIN_POST, by_id))
    print(f"\n## Nima uchun aynan shu qizlar: {fmt_date(EXPLAIN_DAY)}, Qizlar yotoqxonasi\n")
    print(explain_table(explain, "qizlar", by_id))

    table, week_results = fairness_table(cadets, FAIRNESS_WEEK, history)
    print(f"\n## 7 sutkalik adolat jadvali: hafta {FAIRNESS_WEEK.isoformat()} (yakshanba) – {(FAIRNESS_WEEK + dt.timedelta(days=7)).isoformat()}\n")
    print(table)

    # Ikkinchi aylanish boshlangan birinchi holat: kimdir shu haftada 2-marta turadi
    res, post_code = next(
        (r, code)
        for r in week_results
        for code in ROTATION_CHAIN
        if POSTS_BY_CODE[code].size >= 3
        and any(s.week_count >= 1 for s in r.picks[code].ranking if s.cadet_id in r.picks[code].chosen)
    )
    print(f"\n## Nima uchun aynan shu kursantlar (2-aylanish): {fmt_date(res.day)}, {POSTS_BY_CODE[post_code].name}\n")
    print(explain_table(res, post_code, by_id))

    total_females = sum(1 for c in cadets if c.gender == FEMALE)
    print(f"\nRo'yxat: {len(cadets)} kursant ({len(cadets) - total_females} o‘g‘il, {total_females} qiz).")


def _assignments_from(records: list[Record]):
    from naryad.engine.models import Assignment

    out = []
    for post in POSTS:
        for slot in post.slots:
            rec = next((r for r in records if r.post == post.code and r.position == slot.position), None)
            out.append(Assignment(slot=slot, cadet_id=rec.cadet_id if rec else None, group=rec.group if rec else None))
    return out


if __name__ == "__main__":
    main()
