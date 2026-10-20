"""12 haftalik simulyatsiya — statistika sahifasini ko'rish va skrinshotlar uchun (9-bosqich).

FAQAT ALOHIDA (bo'sh) TEST BAZADA ishga tushiring — haqiqiy bazaga yozmang:

    DATABASE_URL=sqlite:///simulyatsiya.sqlite3 python scripts/simulate_weeks.py
    DATABASE_URL=sqlite:///simulyatsiya.sqlite3 python manage.py runserver

Bazada birorta sutka bo'lsa, skript hech narsa qilmaydi. Har sutka platformaning o'z oqimi bilan
tuziladi: qoralama (algoritm) → ba'zan qo'lda almashtirish (sabab bilan) → tasdiqlash. 2-kurs har
ikki haftada bir hafta navbatda turadi, shuning uchun haftalar orasida 14 kun.
Bitta kursant ataylab bir necha marta qo'lda qo'yiladi — “qo'lda tuzatishlar nazorati” ogohlantirishini ko'rish uchun.
Foydalanuvchilar: kursboshligi, kurs.ofitseri (admin), kursant (parol Demo-parol-2026).

15-bosqich: `--zalyotchiklar` — 3-hafta boshida 3 ta zalyotchik (2–3 tadan jazo naryadi) kiritiladi;
oxirida natija jadvali: jazo naryadlari faqat 1-NO‘J / 1-Yotoqxonada, guruhlar adolati (oddiy naryadlar).

    DATABASE_URL=sqlite:///simulyatsiya-zalyot.sqlite3 python scripts/simulate_weeks.py --zalyotchiklar

20-bosqich: `--komandirlar` — 6 ta guruh komandiri akkaunti; 3-hafta boshida har komandir o'z guruhidan 1 tadan
zalyotchi kiritadi (jami 6 ta, 2 tadan jazo naryadi) — komandir qoidalari bilan (simulyatsiyada tanbeh sanasi
chegarasi 365 kun, chunki haftalar o'tmishda).

    DATABASE_URL=sqlite:///simulyatsiya-komandir.sqlite3 python scripts/simulate_weeks.py --komandirlar

21-bosqich: `--joylar` — bazaga YOZMAYDI: faqat algoritm (naryad.engine) bilan 12 hafta (haftalar orasida 14 kun),
haqiqiy guruh hajmlari (naryadga chiqadigan o'g'il bolalar 11/12/12/14/16/13), eski va yangi tartib solishtiriladi:

    python scripts/simulate_weeks.py --joylar
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402

PASSWORD = "Demo-parol-2026"
INITIAL_ROTATION = {"markaz": "BI-625", "noj1": "BI-525", "noj2": "BI-425", "yotoq1": "BI-225", "oquv": "BI-325", "patrul": "YuP-125"}
FAVOURITE = ("BI-325", 6)  # (guruh, ro'yxat raqami) — ataylab qo'lda ko'p qo'yiladigan kursant
# 15-bosqich: (guruh, jazo naryadlari soni, sabab) — guruhlari turli joylarda bo'lgan uch zalyotchik
OFFENDERS = [("BI-625", 3, "tartib"), ("YuP-125", 2, "uxlash"), ("BI-325", 3, "boshqa")]
OFFENDERS_WEEK = 3


def main() -> None:
    if "--joylar" in sys.argv:
        rotation_report(weeks=12)
        return
    from naryad import days, services
    from naryad.dashboard import current_duty_date
    from naryad.models import Assignment, Cadet, DutyDay, InitialRotation, Post, PostSlot, StudyGroup, User

    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=12)
    parser.add_argument("--seed", type=int, default=9)
    parser.add_argument("--zalyotchiklar", action="store_true", help="3 ta zalyotchik bilan (15-bosqich)")
    parser.add_argument("--komandirlar", action="store_true", help="6 ta komandir kiritgan zalyotchi bilan (20-bosqich)")
    parser.add_argument("--joylar", action="store_true", help="joylar navbati: eski va yangi tartib (21-bosqich, bazasiz)")
    args = parser.parse_args()

    print(f"Baza: {connection.settings_dict['NAME']}")
    call_command("migrate", verbosity=0)
    if DutyDay.objects.exists():
        sys.exit("Bazada sutkalar bor — simulyatsiya faqat bo'sh, alohida test bazada ishga tushiriladi.")
    if not Cadet.objects.exists():
        call_command("load_roster", verbosity=0)
    if InitialRotation.as_mapping() is None:
        for code, group in INITIAL_ROTATION.items():
            InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))

    def user(username, role, **extra):
        u = User.objects.filter(username=username).first() or User(username=username, role=role, **extra)
        u.set_password(PASSWORD)
        u.must_change_password = False
        u.save()
        return u

    admin = user("kursboshligi", "admin")
    officer = user("kurs.ofitseri", "admin")
    user("kursant", "cadet", cadet=Cadet.objects.get(last_name="Sa’dullayev", first_name="Behro‘z"))

    favourite = Cadet.objects.get(group__code=FAVOURITE[0], list_number=FAVOURITE[1])
    rnd = random.Random(args.seed)
    today = current_duty_date()
    this_week = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    starts = [this_week - dt.timedelta(days=14 * k) for k in range(args.weeks, 0, -1)]
    male_slots = list(PostSlot.objects.filter(post__gender="M").select_related("post"))
    replaced = favoured = 0

    for n, start in enumerate(starts, 1):
        days.open_week(start, admin)
        if args.zalyotchiklar and n == OFFENDERS_WEEK:
            add_offenders(start, admin)
        if args.komandirlar and n == OFFENDERS_WEEK:
            add_commander_offenders(start)
        favour_pending = n % 3 == 0  # har 3-haftada bir marta
        for i in range(7):
            date = start + dt.timedelta(days=i)
            day = services.generate_draft(date, admin)
            who = officer if i % 3 == 2 else admin
            # ataylab: shu kursantning guruhi joy bergan sutkalarda (har 3-haftada) uni qo'lda qo'yish
            if favour_pending and i >= 2 and put(day, favourite, "boshqa", "Ko‘rsatma bo‘yicha", who, days):
                favoured += 1
                favour_pending = False
            elif rnd.random() < 0.22:
                slot = rnd.choice(male_slots)
                day.refresh_from_db()
                cand = next((c.cadet for c in days.replacement_candidates(day, slot) if not c.excluded and not c.no_rest), None)
                if cand:
                    code = rnd.choice(["kasal", "kasal", "tatil", "sababli", "boshqa"])
                    days.replace_cadet(date, slot.pk, cand.pk, code, "Navbatchilikka chaqirildi" if code == "boshqa" else "", who, day.version)
                    replaced += 1
            day.refresh_from_db()
            days.approve(date, admin, day.version)
        print(f"{n:2}. hafta {start:%d.%m.%Y} — 7 sutka tasdiqlandi")
    total = Assignment.objects.filter(duty_day__status="approved").count()
    print(f"Tayyor: {len(starts) * 7} sutka, {total} tayinlash, {replaced} tasodifiy va {favoured} ataylab qo'lda almashtirish.")
    if args.zalyotchiklar or args.komandirlar:
        report_offenders()


def add_offenders(start, admin) -> None:
    from naryad import penalties
    from naryad.models import Cadet

    for group, count, reason in OFFENDERS:
        cadet = Cadet.objects.filter(group__code=group, gender="M", is_active=True, duty_exempt=False).order_by("list_number").first()
        penalties.add(cadet, reason, "Simulyatsiya: tanbeh", start, count, admin)
        print(f"   zalyot: {cadet.short_name} ({group}) — {count} ta jazo naryadi")


def add_commander_offenders(start) -> None:
    """Har guruh komandiri (akkaunt yaratiladi) o'z guruhidan bitta zalyotchi kiritadi."""
    from naryad import penalties
    from naryad.models import Cadet, Setting, User

    Setting.objects.filter(pk=Setting.load().pk).update(commander_order_max_age_days=365)
    for boss in Cadet.objects.filter(duty_position__iendswith="guruh komandiri").select_related("group").order_by("group__display_order"):
        u = User.objects.filter(cadet=boss).first() or User(username=f"komandir.{boss.group.code.lower()}", role="commander", cadet=boss)
        u.role = "commander"
        u.set_password(PASSWORD)
        u.must_change_password = False
        u.full_clean(exclude=["password"])
        u.save()
        cadet = Cadet.objects.filter(group=boss.group, gender="M", is_active=True, duty_exempt=False).order_by("-list_number").first()
        penalties.add(cadet, "tartib", "Simulyatsiya: komandir tanbehi", start, 2, u)
        print(f"   komandir {u.username}: zalyot {cadet.short_name} ({boss.group.code}) — 2 ta jazo naryadi")


def report_offenders() -> None:
    """Natija jadvali: har zalyot, jazo naryadlari joylari, guruhlar adolati (faqat oddiy naryadlar)."""
    from collections import Counter

    from naryad import stats
    from naryad.models import Assignment, GroupPostAssignment, Penalty

    print("\nZalyotchiklar (jazo naryadlari):")
    print(f"{'Kursant':<18}{'Guruh':<9}{'Jami':>5}{'O‘tildi':>8}  {'Holat':<10} Sutkalar (joy, o‘sha kuni joy guruhi)")
    for p in Penalty.objects.select_related("cadet__group").order_by("pk"):
        rows = Assignment.objects.filter(penalty=p, duty_day__status="approved").select_related("duty_day", "post_slot__post")
        cells = []
        for a in rows.order_by("duty_day__date"):
            gpa = GroupPostAssignment.objects.get(duty_day=a.duty_day, post=a.post_slot.post)
            cells.append(f"{a.duty_day.date:%d.%m} {a.post_slot.post.code} ({gpa.group.code})")
        print(f"{p.cadet.short_name:<18}{p.cadet.group.code:<9}{p.count:>5}{rows.count():>8}  {p.status:<10} {', '.join(cells)}")
    posts = Counter(Assignment.objects.filter(kind="penalty", duty_day__status="approved").values_list("post_slot__post__code", flat=True))
    roles = Counter(Assignment.objects.filter(kind="penalty", duty_day__status="approved").values_list("post_slot__role", flat=True))
    print(f"Jazo naryadlari joylari: {dict(posts)}; lavozimlar: {dict(roles)}")
    print("\nGuruhlar adolati (faqat oddiy naryadlar, butun tarix):")
    print(f"{'Hovuz':<10}{'Kursant':>8}{'Min':>5}{'Max':>5}{'Farq':>6}{'O‘rtacha':>10}  Holat")
    for f in stats.fairness_all(stats.Period()):
        print(f"{f.title:<10}{f.members:>8}{f.min!s:>5}{f.max!s:>5}{f.diff!s:>6}{f.mean!s:>10}  {f.status}")


ROTATION_START = dt.date(2026, 9, 13)  # yakshanba


def engine_roster():
    """data/roster.json — naryadga chiqadiganlar (lavozimdagilar hovuzga kirmaydi, services.engine_cadets kabi)."""
    import json

    from naryad.engine.models import Cadet as ECadet

    data = json.loads((ROOT / "data" / "roster.json").read_text(encoding="utf-8"))
    return [
        ECadet(id=c["id"], last_name=c["last_name"], first_name=c["first_name"], patronymic=c["patronymic"],
               group=c["group"], gender=c["gender"], short_name=c["short_name"])
        for c in data if not c.get("duty_exempt")
    ]


def run_engine(cadets, weeks: int, rotation):
    """Har 2-kurs haftasi 7 sutka, haftalar orasida 14 kun; har sutka “tasdiqlanadi” (tarixga qo'shiladi)."""
    from naryad.engine import generate_day

    history, results = [], []
    for w in range(weeks):
        start = ROTATION_START + dt.timedelta(days=14 * w)
        for i in range(7):
            res = generate_day(start + dt.timedelta(days=i), cadets, history, initial_rotation=INITIAL_ROTATION, rotation=rotation)
            results.append(res)
            history.extend(res.to_records())
    return results, history


def rotation_metrics(cadets, results, history, hard_posts=("noj1", "yotoq1")) -> dict:
    """Guruh bo'yicha: QOIDA A buzilishi, ketma-ket kunlar, shu joy ketma-ket, haftada 3 marta,
    “avval hamma bir martadan” buzilishi, jami va og'ir joylar farqi, bo'sh o'rinlar."""
    from collections import defaultdict
    from itertools import pairwise

    from naryad.engine.allocator import week_start

    group_of = {c.id: c.group for c in cadets if c.gender == "M"}
    groups = sorted(set(group_of.values()))
    out = {g: defaultdict(int) for g in groups}
    by_cadet = defaultdict(list)
    for r in history:
        if r.cadet_id in group_of:
            by_cadet[r.cadet_id].append(r)
    for cid, recs in by_cadet.items():
        m = out[group_of[cid]]
        weekly = defaultdict(list)
        for r in recs:
            weekly[week_start(r.day)].append(r)
        for items in weekly.values():
            hard = sum(1 for r in items if r.post in hard_posts)
            m["hard2"] += max(0, hard - 1)
            m["three"] += 1 if len(items) >= 3 else 0
        for a, b in pairwise(recs):
            m["consecutive"] += 1 if (b.day - a.day).days == 1 else 0
            m["same_post"] += 1 if a.post == b.post else 0
    # “Avval hamma bir martadan”: hafta yakunida guruhda kimdir 2+ marta turgan, lekin kimdir umuman turmagan
    weeks = sorted({week_start(r.day) for r in history})
    for g in groups:
        members = [cid for cid, gg in group_of.items() if gg == g]
        for w in weeks:
            counts = [sum(1 for r in by_cadet[c] if week_start(r.day) == w) for c in members]
            if max(counts) >= 2:
                out[g]["once_first"] += sum(1 for n in counts if n == 0)
    for res in results:
        for code, pick in res.picks.items():
            group = res.group_by_post.get(code)
            if group is None:
                continue
            # tanlash paytida: shu haftada turmagan nomzod qolib, ikkinchi martasi bo'layotgan tanlangan (faqat ma'lumot uchun)
            chosen = set(pick.chosen)
            rest_min = min((s.week_count for s in pick.ranking if s.cadet_id not in chosen), default=None)
            if rest_min is not None:
                out[group]["pick_order"] += sum(1 for s in pick.ranking if s.cadet_id in chosen and s.week_count > rest_min)
        for a in res.assignments:
            if a.cadet_id is None and a.slot.post in res.group_by_post:
                out[res.group_by_post[a.slot.post]]["empty"] += 1
    for g in groups:
        members = [cid for cid, gg in group_of.items() if gg == g]
        totals = [len(by_cadet[c]) for c in members]
        hards = [sum(1 for r in by_cadet[c] if r.post in hard_posts) for c in members]
        out[g]["members"] = len(members)
        out[g]["spread"] = max(totals) - min(totals)
        out[g]["hard_spread"] = max(hards) - min(hards)
    return out


def rotation_report(weeks: int = 12) -> None:
    from naryad.engine.config import PostRotation

    cadets = engine_roster()
    old = rotation_metrics(cadets, *run_engine(cadets, weeks, None))
    new = rotation_metrics(cadets, *run_engine(cadets, weeks, PostRotation()))
    order = ["YuP-125", "BI-225", "BI-325", "BI-425", "BI-525", "BI-625"]
    cols = [("hard2", "2 og‘ir/hafta"), ("same_post", "shu joy ketma-ket"), ("three", "3 marta/hafta"),
            ("consecutive", "ketma-ket kun"), ("once_first", "“avval hamma 1 marta”"), ("pick_order", "tanlash tartibi*"),
            ("spread", "jami farqi"), ("hard_spread", "og‘ir joy farqi"), ("empty", "bo‘sh o‘rin")]
    print(f"Joylar navbati: {weeks} hafta, eski → yangi (faqat oddiy naryadlar; jazo naryadi yo‘q)")
    print("| Guruh | " + " | ".join(t for _, t in cols) + " |")
    print("|---|" + "---|" * len(cols))
    for g in order:
        o, n = old[g], new[g]
        print(f"| {g} ({o['members']}) | " + " | ".join(f"{o[k]} → {n[k]}" for k, _ in cols) + " |")
    print("* tanlash paytida shu haftada hali turmagan nomzod qolib, boshqasi 2-marta tanlangan holatlar: yangi tartibda bu faqat")
    print("  “oxirgi naryadi shu joy” qoidasi (3-o‘rin) haftadagi sondan (4-o‘rin) oldin turgani uchun; hafta yakunida hamma bir martadan turgan.")


def put(day, cadet, code, note, user, days) -> bool:
    """Kursantni uning guruhi bergan joyga qo'lda qo'yadi (qoidalar ruxsat bersa)."""
    from naryad.models import Assignment, GroupPostAssignment, PostSlot

    gpa = GroupPostAssignment.objects.filter(duty_day=day, group=cadet.group).first()
    if gpa is None or Assignment.objects.filter(duty_day=day, cadet=cadet).exists():
        return False
    for slot in PostSlot.objects.filter(post=gpa.post).order_by("-position"):
        day.refresh_from_db()
        allowed = {c.cadet.pk for c in days.replacement_candidates(day, slot) if not c.excluded and not c.no_rest}
        if cadet.pk in allowed:
            days.replace_cadet(day.date, slot.pk, cadet.pk, code, note, user, day.version)
            return True
    return False


if __name__ == "__main__":
    main()
