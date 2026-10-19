"""16-bosqich: kursant tasdiqlangan ro'yxatlarni ko'radi, sababli holat eslatmasi, “ozod” yozuvi olib tashlandi (CLAUDE.md 63-band)."""

from __future__ import annotations

import datetime as dt
import io

import pytest
from django.urls import reverse
from pypdf import PdfReader

from naryad import days, penalties, services
from naryad.models import Cadet, DutyDay, DutyWeek, Gender, InitialRotation, Post, PostSlot, Setting, StudyGroup, User

from .conftest import INITIAL_ROTATION, exempt_words

SUNDAY = dt.date(2026, 9, 13)
MONDAY = SUNDAY + dt.timedelta(days=1)
PASSWORD = "Kuchli-parol-2026"
pytestmark = pytest.mark.django_db

NOTICE = {
    "uz": "Agar sababli holatingiz bo‘lsa (kasallik, tadbirda qatnashish, sport musobaqasi) va naryad hali tasdiqlanmagan "
          "bo‘lsa, kurs starshinasiga yoki kurs boshlig‘iga uchrang.",
    "ru": "Если у вас есть уважительная причина (болезнь, участие в мероприятии, спортивные соревнования), а наряд ещё не "
          "утверждён, обратитесь к старшине курса или начальнику курса.",
    "en": "If you have a valid reason (illness, an event, a sports competition) and the duty roster has not been approved yet, "
          "contact the course senior cadet or the course commander.",
}


@pytest.fixture
def admin(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    DutyWeek.objects.create(start_date=SUNDAY)
    Setting.load()
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


def generate_and_approve(day: dt.date, admin) -> DutyDay:
    draft = services.generate_draft(day, admin)
    return days.approve(day, admin, draft.version)


def login(client, cadet: Cadet | None = None, lang: str = "uz", role: str = "cadet"):
    user = User.objects.create_user(f"u{User.objects.count()}", password=PASSWORD, role=role, cadet=cadet, language=lang)
    client.force_login(user)
    return client


def assignment(day: dt.date, post_code: str, position: int = 1):
    return DutyDay.objects.get(date=day).assignments.select_related("cadet__group").get(
        post_slot=PostSlot.objects.get(post__code=post_code, position=position)
    )


def boy(group: str, index: int = 0) -> Cadet:
    return Cadet.objects.filter(group__code=group, gender=Gender.MALE, duty_exempt=False, is_active=True).order_by("list_number")[index]


def page(client, name: str, *args) -> str:
    response = client.get(reverse(name, args=list(args)))
    assert response.status_code == 200, name
    return response.content.decode()


# ---------------------------------------------------------------------------
# 1. Tasdiqlangan ro'yxat
# ---------------------------------------------------------------------------


def test_cadet_opens_approved_day_and_sees_self_and_comrades(client, admin):
    generate_and_approve(SUNDAY, admin)
    me = assignment(SUNDAY, "noj1", 2)
    comrade = assignment(SUNDAY, "noj1", 1)
    login(client, me.cadet)
    body = page(client, "day_detail", SUNDAY.isoformat())
    assert body.count('data-testid="my-row"') == 1 and ">Siz<" in body
    assert me.cadet.short_name in body and comrade.cadet.short_name in body and me.group.code in body
    assert "1-sonli NO‘J bo‘yicha" in body or "NO‘J" in body  # joy bo'yicha guruhlangan
    # faqat o'qish: tuzish/almashtirish/tasdiqlash/o'chirish tugmalari, jurnal, belgilar yo'q
    for word in ("Almashtirish", "Kursant qo‘yish", "Tasdiqni bekor qilish", "Qoralamani o‘chirish", "Qayta tuzish",
                 "Lavozimlarni almashtirish", "Jurnal", "Tasdiqlagan:", "✎", "hx-get"):
        assert word not in body, word
    assert "PDF yuklab olish" in body and "Chop etish" in body
    assert NOTICE["uz"] in body


def test_approved_list_shows_only_approved_and_marks_my_days(client, admin):
    generate_and_approve(SUNDAY, admin)
    services.generate_draft(MONDAY, admin)  # qoralama — ko'rinmaydi
    me = assignment(SUNDAY, "markaz")
    login(client, me.cadet)
    body = page(client, "approved_days")
    assert "13-sentabr" in body and "14-sentabr kunidan" not in body
    assert body.count('data-testid="my-day"') == 1 and "Siz naryaddasiz" in body
    assert NOTICE["uz"] in body
    # sutka sahifasida qo'shni sutka havolasi faqat tasdiqlanganiga (qoralamaga yo'q)
    day_page = page(client, "day_detail", SUNDAY.isoformat())
    assert reverse("day_detail", args=[MONDAY.isoformat()]) not in day_page


def test_cadet_gets_403_for_everything_else(client, admin):
    generate_and_approve(SUNDAY, admin)
    services.generate_draft(MONDAY, admin)
    me = assignment(SUNDAY, "noj1")
    other = Cadet.objects.exclude(pk=me.cadet_id).first()
    login(client, me.cadet)
    for name, args in [
        ("cadet_detail", [other.pk]),
        ("day_detail", [MONDAY.isoformat()]),  # qoralama
        ("day_pdf", [MONDAY.isoformat()]),  # qoralama PDF’i
        ("day_print", [MONDAY.isoformat()]),
        ("day_detail", [(MONDAY + dt.timedelta(days=1)).isoformat()]),  # tuzilmagan sutka ham yopiq
        ("stats", []),
        ("stats_excel", []),
        ("day_log", [SUNDAY.isoformat()]),
        ("absence_list", []),
        ("penalty_list", []),
        ("cadet_list", []),
        ("week_list", []),
        ("day_replace", [SUNDAY.isoformat(), me.post_slot_id]),
    ]:
        assert client.get(reverse(name, args=args)).status_code == 403, (name, args)


def test_week_pdf_for_cadet_has_only_approved_days(client, admin):
    generate_and_approve(SUNDAY, admin)
    services.generate_draft(MONDAY, admin)
    login(client, boy("BI-225"))
    response = client.get(reverse("week_pdf", args=[SUNDAY.isoformat()]))
    assert response.status_code == 200
    assert len(PdfReader(io.BytesIO(response.content)).pages) == 1


def test_penalty_duty_is_plain_guard_for_cadet_and_pdf_has_no_zalyot(client, admin):
    offender = boy(INITIAL_ROTATION["markaz"])
    penalties.add(offender, "tartib", "x", SUNDAY, 1, admin)
    generate_and_approve(SUNDAY, admin)
    login(client, boy("BI-625"))
    body = page(client, "day_detail", SUNDAY.isoformat())
    assert offender.short_name in body
    assert "Zalyot" not in body and 'data-testid="penalty-row"' not in body and "jazo" not in body.lower()
    pdf = client.get(reverse("day_pdf", args=[SUNDAY.isoformat()]))
    assert pdf.status_code == 200 and pdf["Content-Type"] == "application/pdf"
    text = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages).lower()
    assert "zalyot" not in text and "jazo" not in text and "qoralama" not in text
    assert "posbon" in text and offender.last_name.lower() in text


# ---------------------------------------------------------------------------
# 2. Sababli holat eslatmasi
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lang", ["uz", "ru", "en"])
def test_reason_notice_in_three_languages(client, admin, lang):
    generate_and_approve(SUNDAY, admin)
    login(client, boy("BI-325"), lang=lang)
    for name, args in [("home", []), ("approved_days", []), ("day_detail", [SUNDAY.isoformat()])]:
        body = page(client, name, *args)
        assert NOTICE[lang] in body and 'data-testid="duty-reason-notice"' in body, (lang, name)


def test_reason_notice_not_on_admin_pages(client, admin):
    generate_and_approve(SUNDAY, admin)
    client.force_login(admin)
    for name, args in [("home", []), ("approved_days", []), ("day_detail", [SUNDAY.isoformat()]), ("cadet_list", [])]:
        assert 'data-testid="duty-reason-notice"' not in page(client, name, *args), name


# ---------------------------------------------------------------------------
# 3. “Ozod” yozuvi yo'q, lavozim yozuvi bor
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lang", ["uz", "ru", "en"])
def test_no_exempt_word_anywhere_position_label_stays(client, admin, lang):
    generate_and_approve(SUNDAY, admin)
    draft = services.generate_draft(MONDAY, admin)
    starshina = Cadet.objects.get(duty_exempt=True, duty_position__icontains="starshina")
    login(client, lang=lang, role="admin")
    slot = PostSlot.objects.get(post__code="noj1", position=1)
    pages = {
        "cadet_list": page(client, "cadet_list"),
        "cadet_list_filter": client.get(reverse("cadet_list"), {"holat": "lavozimda"}).content.decode(),
        "cadet_detail": page(client, "cadet_detail", starshina.pk),
        "stats": page(client, "stats"),
        "day_replace": client.get(reverse("day_replace", args=[MONDAY.isoformat(), slot.pk]), HTTP_HX_REQUEST="true").content.decode(),
        "day_detail": page(client, "day_detail", MONDAY.isoformat()),
        "penalty_list": page(client, "penalty_list"),
    }
    for name, html in pages.items():
        assert not exempt_words(html), (lang, name, exempt_words(html))
    chiqmaydi = {"uz": "naryadga chiqmaydi", "ru": "не заступает в наряд", "en": "not on the duty roster"}[lang]
    assert chiqmaydi in pages["day_replace"]  # almashtirish oynasida: “lavozim — naryadga chiqmaydi”
    assert starshina.duty_position in pages["cadet_list"] and starshina.duty_position in pages["cadet_detail"]
    assert starshina.duty_position in pages["stats"]
    assert draft.status == DutyDay.Status.DRAFT


def test_filter_and_column_renamed_in_three_languages(client, admin):
    expected = {"uz": "Naryadga chiqmaydi", "ru": "Не заступает в наряд", "en": "Not on the duty roster"}
    for lang, label in expected.items():
        login(client, lang=lang, role="admin")
        assert label in page(client, "cadet_list"), lang
    # Django boshqaruv paneli: filtr va ustun ham shu nom bilan
    login(client, lang="uz", role="admin")
    html = client.get("/admin/naryad/cadet/").content.decode()
    assert "naryadga chiqmaydi" in html.lower() and not exempt_words(html)


def test_exempt_rules_unchanged(admin):
    """Faqat yozuv o'zgardi: lavozimdagilar baribir nomzodlar hovuziga kirmaydi."""
    pool = {c.id for c in services.engine_cadets()}
    exempt = set(Cadet.objects.filter(duty_exempt=True).values_list("pk", flat=True))
    assert len(exempt) == 9 and not (pool & exempt)
    day = generate_and_approve(SUNDAY, admin)
    assert not day.assignments.filter(cadet__duty_exempt=True).exists()
