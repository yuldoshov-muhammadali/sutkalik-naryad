"""14-bosqich: kursant faqat o'z naryadini ko'radi; ertangi ro'yxat bir kun oldin tayyor (CLAUDE.md 60-band)."""

from __future__ import annotations

import datetime as dt
import re

import pytest
from django.urls import reverse
from django.utils import timezone, translation

from naryad import days, services
from naryad.dashboard import countdown_text
from naryad.models import Assignment, Cadet, DutyDay, DutyWeek, InitialRotation, Post, PostSlot, PrepNote, Setting, StudyGroup, User
from naryad.readiness import approval_banner

from .conftest import INITIAL_ROTATION

SUNDAY = dt.date(2026, 9, 13)  # 2-kurs haftasi: 13–19 sentabr
MONDAY, TUESDAY = SUNDAY + dt.timedelta(days=1), SUNDAY + dt.timedelta(days=2)
PASSWORD = "Kuchli-parol-2026"
pytestmark = pytest.mark.django_db


def at(day: dt.date, hour: int, minute: int = 0) -> dt.datetime:
    return timezone.make_aware(dt.datetime.combine(day, dt.time(hour, minute)))


def freeze(monkeypatch, moment: dt.datetime) -> None:
    """Vaqtni “muzlatish”: hamma joyda timezone.now() shu vaqtni qaytaradi."""
    monkeypatch.setattr("django.utils.timezone.now", lambda: moment)


@pytest.fixture
def admin(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    DutyWeek.objects.create(start_date=SUNDAY)
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


def approve(day: dt.date, admin) -> DutyDay:
    draft = services.generate_draft(day, admin)
    return days.approve(draft.date, admin, draft.version)


def login_cadet(client, cadet: Cadet, lang: str = "uz"):
    user = getattr(cadet, "user", None) or User.objects.create_user(
        f"k{cadet.pk}", password=PASSWORD, role="cadet", cadet=cadet, language=lang
    )
    client.force_login(user)
    return client


def slot(post_code: str, position: int = 1) -> PostSlot:
    return PostSlot.objects.get(post__code=post_code, position=position)


def on_slot(day: dt.date, post_code: str, position: int = 1) -> Assignment:
    return Assignment.objects.select_related("cadet", "post_slot__post", "group").get(
        duty_day__date=day, post_slot=slot(post_code, position)
    )


def home(client) -> str:
    """Bosh sahifa: HTML va (teglarsiz) ko'rinadigan matn birga — sana qismlari alohida <span> larda."""
    html = client.get(reverse("home")).content.decode()
    return html + "\n" + re.sub(r"<[^>]+>", "", html)


# ---------------------------------------------------------------------------
# 1. Kursant kartochkasi
# ---------------------------------------------------------------------------


def test_card_shows_date_post_role_group_and_countdown(client, admin, monkeypatch):
    approve(SUNDAY, admin)
    a = on_slot(SUNDAY, "noj1")
    freeze(monkeypatch, at(SUNDAY, 9, 46))
    body = home(login_cadet(client, a.cadet))
    assert "Mening navbatdagi naryadim" in body
    assert "13-sentabr, yakshanba 18:00 → 14-sentabr 18:00" in body
    assert a.post_slot.post.name in body and a.post_slot.get_role_display() in body and a.group.code in body
    assert "Naryadga 8 soat 14 daqiqa qoldi" in body
    assert "Tasdiqlangan naryadlar" in body and reverse("approved_days") in body  # 16-bosqichda qaytdi
    assert reverse("my_card") in body  # “Mening tarixim” havolasi


def test_countdown_during_duty(client, admin, monkeypatch):
    approve(SUNDAY, admin)
    a = on_slot(SUNDAY, "markaz")
    freeze(monkeypatch, at(MONDAY, 3, 30))  # 13-sentabr sutkasi davom etmoqda (14-sentabr 18:00 gacha)
    body = home(login_cadet(client, a.cadet))
    assert "Hozir naryaddasiz, smena almashishiga 14 soat 30 daqiqa qoldi" in body
    assert 'data-countdown' in body and "{h}" in body  # JS shablonlari (har soniyada yangilanadi)


@pytest.mark.parametrize(
    "lang, seconds, on_duty, expected",
    [
        ("uz", 26 * 3600 + 5 * 60, False, "Naryadga 1 kun 2 soat qoldi"),
        ("uz", 21 * 3600 + 14 * 60, False, "Naryadga 21 soat 14 daqiqa qoldi"),
        ("uz", 45 * 60, False, "Naryadga 45 daqiqa qoldi"),
        ("uz", 24 * 3600, True, "Hozir naryaddasiz, smena almashishiga 24 soat 0 daqiqa qoldi"),
        ("uz", 59, True, "Hozir naryaddasiz, smena almashishiga 0 daqiqa qoldi"),
        ("ru", 21 * 3600 + 14 * 60, False, "До наряда осталось 21 ч 14 мин"),
        ("en", 3 * 3600 + 5 * 60, True, "You are on duty now; shift change in 3 h 5 min"),
    ],
)
def test_countdown_texts(lang, seconds, on_duty, expected):
    with translation.override(lang):
        assert countdown_text(seconds, on_duty) == expected


def test_draft_is_never_visible(client, admin, monkeypatch):
    draft = services.generate_draft(SUNDAY, admin)
    a = on_slot(SUNDAY, "noj1")
    freeze(monkeypatch, at(SUNDAY, 9))
    body = home(login_cadet(client, a.cadet))
    assert "Yaqin kunlarda tasdiqlangan naryadingiz yo‘q" in body
    assert 'data-testid="duty-post"' not in body and "Naryadingiz bekor qilindi" not in body
    assert client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).status_code == 403
    draft.refresh_from_db()
    assert draft.status == "draft"


def test_cadet_sees_only_own_data(client, admin):
    approve(SUNDAY, admin)
    a = on_slot(SUNDAY, "noj1")
    other = Cadet.objects.exclude(pk=a.cadet_id).first()
    login_cadet(client, a.cadet)
    for name, args in [
        ("cadet_detail", [other.pk]),
        ("cadet_list", []),
        ("stats", []),
        ("day_log", [SUNDAY.isoformat()]),
        ("absence_list", []),
        ("penalty_list", []),
    ]:
        assert client.get(reverse(name, args=args)).status_code == 403, name
    # 16-bosqich: tasdiqlangan sutka (sahifa, PDF, chop etish) kursantga yana ochiq — CLAUDE.md 63-band
    for name in ("day_detail", "day_pdf", "day_print", "week_pdf"):
        assert client.get(reverse(name, args=[SUNDAY.isoformat()])).status_code == 200, name
    assert client.get(reverse("approved_days")).status_code == 200
    card = client.get(reverse("cadet_detail", args=[a.cadet_id])).content.decode()  # “Mening tarixim”
    assert "13.09.2026" in card and a.post_slot.post.name in card and a.post_slot.get_role_display() in card
    assert other.full_name not in card


def test_old_cadet_sees_cancelled_new_cadet_sees_duty(client, admin, monkeypatch):
    approve(SUNDAY, admin)
    old = on_slot(SUNDAY, "noj1")
    freeze(monkeypatch, at(SUNDAY - dt.timedelta(days=1), 20))  # shanba kechqurun — ro'yxat e'lon qilingan
    assert old.post_slot.post.name in home(login_cadet(client, old.cadet))

    # Admin tasdiqni bekor qilib, kursantni almashtiradi
    day = days.reopen(SUNDAY, "kasal bo‘lib qoldi", admin, DutyDay.objects.get(date=SUNDAY).version)
    new = next(c.cadet for c in days.replacement_candidates(day, old.post_slot) if not c.excluded)
    days.replace_cadet(SUNDAY, old.post_slot_id, new.pk, "boshqa", "almashtirildi", admin, day.version)

    body = home(login_cadet(client, old.cadet))
    assert "Naryadingiz bekor qilindi" in body and "13.09.2026 sutkasi" in body
    assert 'data-testid="duty-post"' not in body
    assert "kasal bo‘lib qoldi" not in body and "almashtirildi" not in body  # sababsiz — faqat xabar
    # Yangi kursant qoralamada — hali ko'rmaydi; tasdiqlangach ko'radi
    new_client = client.__class__()
    assert 'data-testid="duty-post"' not in home(login_cadet(new_client, new))
    days.approve(SUNDAY, admin, DutyDay.objects.get(date=SUNDAY).version)
    body = home(new_client)
    assert old.post_slot.post.name in body and "Naryadingiz bekor qilindi" not in body
    assert "Naryadingiz bekor qilindi" in home(login_cadet(client, old.cadet))


def test_reopen_without_replacement_is_not_cancellation(client, admin, monkeypatch):
    approve(SUNDAY, admin)
    a = on_slot(SUNDAY, "noj1")
    freeze(monkeypatch, at(SUNDAY - dt.timedelta(days=1), 20))
    days.reopen(SUNDAY, "tekshirish", admin, DutyDay.objects.get(date=SUNDAY).version)
    body = home(login_cadet(client, a.cadet))
    assert "Naryadingiz bekor qilindi" not in body  # hali ro'yxatda (qoralama) — xabar yo'q
    assert "Yaqin kunlarda tasdiqlangan naryadingiz yo‘q" in body  # qoralama ko'rinmaydi


def test_cancelled_notice_disappears_after_duty_day(client, admin, monkeypatch):
    approve(SUNDAY, admin)
    old = on_slot(SUNDAY, "noj1")
    day = days.reopen(SUNDAY, "x", admin, DutyDay.objects.get(date=SUNDAY).version)
    new = next(c.cadet for c in days.replacement_candidates(day, old.post_slot) if not c.excluded)
    days.replace_cadet(SUNDAY, old.post_slot_id, new.pk, "boshqa", "x", admin, day.version)
    freeze(monkeypatch, at(MONDAY, 19))  # 13-sentabr sutkasi tugagan
    assert "Naryadingiz bekor qilindi" not in home(login_cadet(client, old.cadet))


# ---------------------------------------------------------------------------
# 2. Tayyorgarlik eslatmasi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lang, expected",
    [("uz", "17:30 da yo‘riqnomaga keling"), ("ru", "Явиться на инструктаж в 17:30"), ("en", "17:30 da yo‘riqnomaga keling")],
)
def test_prep_note_in_cadet_language(client, admin, monkeypatch, lang, expected):
    approve(SUNDAY, admin)
    a = on_slot(SUNDAY, "noj1")
    PrepNote.objects.create(post=a.post_slot.post, text_uz="17:30 da yo‘riqnomaga keling", text_ru="Явиться на инструктаж в 17:30")
    freeze(monkeypatch, at(SUNDAY, 9))
    body = home(login_cadet(client, a.cadet, lang))
    assert 'data-testid="prep-note"' in body and expected in body  # inglizchasi bo'sh — o'zbekchasi


def test_empty_prep_note_is_hidden(client, admin, monkeypatch):
    approve(SUNDAY, admin)
    a = on_slot(SUNDAY, "noj1")
    PrepNote.objects.create(post=a.post_slot.post)
    freeze(monkeypatch, at(SUNDAY, 9))
    assert 'data-testid="prep-note"' not in home(login_cadet(client, a.cadet))


def test_settings_page_has_prep_notes_and_deadline(client, admin):
    Setting.load()
    client.force_login(admin)
    body = client.get(reverse("admin:naryad_setting_change", args=[1])).content.decode()
    assert "approval_lead_hours" in body and "prep_notes-0-text_ru" in body
    assert PrepNote.objects.count() == Post.objects.count()


# ---------------------------------------------------------------------------
# 3. Ertangi ro'yxat muddati — admin banneri
# ---------------------------------------------------------------------------


def test_banner_yellow_before_deadline(admin):
    approve(SUNDAY, admin)
    approve(MONDAY, admin)
    b = approval_banner(at(MONDAY, 15))
    assert b.level == "yellow" and b.day == TUESDAY and b.action_label == "Tuzish"
    assert b.text == "Ertangi sutka (15-sentabr) hali tasdiqlanmagan. Muddat: bugun 18:00 gacha, 3 soat qoldi."


def test_banner_red_after_deadline_and_green_when_approved(admin):
    approve(SUNDAY, admin)
    approve(MONDAY, admin)
    services.generate_draft(TUESDAY, admin)
    b = approval_banner(at(MONDAY, 19))
    assert b.level == "red" and b.action_label == "Ochish"
    assert b.text == "Ertangi sutka (15-sentabr) hali tasdiqlanmagan. Muddat o‘tdi, kursantlar hali bilmaydi."
    days.approve(TUESDAY, admin, DutyDay.objects.get(date=TUESDAY).version)
    b = approval_banner(at(MONDAY, 19))
    assert b.level == "green" and b.text == "Ertangi ro‘yxat (15-sentabr) tayyor, kursantlarga ko‘rinmoqda."


def test_banner_red_for_today_if_tonight_is_not_approved(admin):
    approve(SUNDAY, admin)  # 14-sentabr (bugun 18:00 dan) tuzilmagan
    b = approval_banner(at(MONDAY, 15))
    assert b.level == "red" and b.day == MONDAY and "Bugungi sutka (14-sentabr)" in b.text


def test_banner_on_saturday_before_week_and_not_outside_week(admin):
    b = approval_banner(at(SUNDAY - dt.timedelta(days=1), 10))  # shanba — yakshanba sutkasi uchun
    assert b.level == "yellow" and b.day == SUNDAY and "8 soat qoldi" in b.text
    assert approval_banner(at(SUNDAY - dt.timedelta(days=5), 10)) is None  # hafta oldidan
    assert approval_banner(at(SUNDAY + dt.timedelta(days=6), 20)) is None  # 20-sentabr — keyingi hafta ochilmagan


def test_banner_respects_lead_hours_setting(admin):
    approve(SUNDAY, admin)
    approve(MONDAY, admin)
    setting = Setting.load()
    setting.approval_lead_hours = 6
    setting.save()
    b = approval_banner(at(MONDAY, 15))
    assert b.level == "yellow" and b.text.endswith("Muddat: ertaga 12:00 gacha, 21 soat qoldi.")


def test_banner_on_admin_home_in_three_languages(client, admin, monkeypatch):
    approve(SUNDAY, admin)
    approve(MONDAY, admin)
    freeze(monkeypatch, at(MONDAY, 15))
    client.force_login(admin)
    expected = {
        "uz": "Muddat: bugun 18:00 gacha, 3 soat qoldi.",
        "ru": "Срок: сегодня до 18:00, осталось 3 ч.",
        "en": "Deadline: today at 18:00, 3 h left.",
    }
    for lang, text in expected.items():
        admin.language = lang
        admin.save(update_fields=["language"])
        body = home(client)
        assert 'data-testid="approval-banner" data-level="yellow"' in body and text in body, lang
    # kursantda banner yo'q
    assert 'data-testid="approval-banner"' not in home(login_cadet(client.__class__(), Cadet.objects.first()))


def test_next_day_still_requires_previous_approval(admin):
    """Hozirgi qoida o'zgarmaydi: keyingi sutka faqat oldingisi tasdiqlangandan keyin tuziladi."""
    services.generate_draft(SUNDAY, admin)
    with pytest.raises(services.ServiceError):
        services.generate_draft(MONDAY, admin)


# ---------------------------------------------------------------------------
# 4. Uch tilda
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "lang, heading, when",
    [
        ("uz", "Mening navbatdagi naryadim", "13-sentabr, yakshanba 18:00 → 14-sentabr 18:00"),
        ("ru", "Мой ближайший наряд", "13 сентября, воскресенье 18:00 → 14 сентября 18:00"),
        ("en", "My next duty", "13 September, Sunday 18:00 → 14 September 18:00"),
    ],
)
def test_cadet_card_in_three_languages(client, admin, monkeypatch, lang, heading, when):
    approve(SUNDAY, admin)
    a = on_slot(SUNDAY, "noj1")
    freeze(monkeypatch, at(SUNDAY, 9))
    body = home(login_cadet(client, a.cadet, lang))
    assert f'<html lang="{lang}"' in body and heading in body and when in body
