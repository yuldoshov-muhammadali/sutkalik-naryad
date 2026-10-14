"""12 haftalik simulyatsiya — statistika sahifasini ko'rish va skrinshotlar uchun (9-bosqich).

FAQAT ALOHIDA (bo'sh) TEST BAZADA ishga tushiring — haqiqiy bazaga yozmang:

    DATABASE_URL=sqlite:///simulyatsiya.sqlite3 python scripts/simulate_weeks.py
    DATABASE_URL=sqlite:///simulyatsiya.sqlite3 python manage.py runserver

Bazada birorta sutka bo'lsa, skript hech narsa qilmaydi. Har sutka platformaning o'z oqimi bilan
tuziladi: qoralama (algoritm) → ba'zan qo'lda almashtirish (sabab bilan) → tasdiqlash. 2-kurs har
ikki haftada bir hafta navbatda turadi, shuning uchun haftalar orasida 14 kun.
Bitta kursant ataylab bir necha marta qo'lda qo'yiladi — “qo'lda tuzatishlar nazorati” ogohlantirishini ko'rish uchun.
Foydalanuvchilar: kursboshligi, kurs.ofitseri (admin), kursant (parol Demo-parol-2026).
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


def main() -> None:
    from naryad import days, services
    from naryad.dashboard import current_duty_date
    from naryad.models import Assignment, Cadet, DutyDay, InitialRotation, Post, PostSlot, StudyGroup, User

    parser = argparse.ArgumentParser()
    parser.add_argument("--weeks", type=int, default=12)
    parser.add_argument("--seed", type=int, default=9)
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
