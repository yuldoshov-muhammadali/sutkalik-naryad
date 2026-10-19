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
    from naryad import days, services
    from naryad.dashboard import current_duty_date
    from naryad.models import Assignment, Cadet, DutyDay, InitialRotation, Post, PostSlot, StudyGroup, User

    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=12)
    parser.add_argument("--seed", type=int, default=9)
    parser.add_argument("--zalyotchiklar", action="store_true", help="3 ta zalyotchik bilan (15-bosqich)")
    parser.add_argument("--komandirlar", action="store_true", help="6 ta komandir kiritgan zalyotchi bilan (20-bosqich)")
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
                cand = next((c.cadet for c in days.replacement_candidates(day, slot) if not c.excluded), None)
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


def put(day, cadet, code, note, user, days) -> bool:
    """Kursantni uning guruhi bergan joyga qo'lda qo'yadi (qoidalar ruxsat bersa)."""
    from naryad.models import Assignment, GroupPostAssignment, PostSlot

    gpa = GroupPostAssignment.objects.filter(duty_day=day, group=cadet.group).first()
    if gpa is None or Assignment.objects.filter(duty_day=day, cadet=cadet).exists():
        return False
    for slot in PostSlot.objects.filter(post=gpa.post).order_by("-position"):
        day.refresh_from_db()
        allowed = {c.cadet.pk for c in days.replacement_candidates(day, slot) if not c.excluded}
        if cadet.pk in allowed:
            days.replace_cadet(day.date, slot.pk, cadet.pk, code, note, user, day.version)
            return True
    return False


if __name__ == "__main__":
    main()
