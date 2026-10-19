"""17-bosqich: kasallar ro'yxati — Absence (kasal) + tavsif; generator, almashtirish, ko'rinish (CLAUDE.md 64-band)."""

from __future__ import annotations

import datetime as dt
import io

import pytest
from django.urls import reverse
from django.utils import timezone
from pypdf import PdfReader

from naryad import days, penalties, services
from naryad import sick as sick_service
from naryad.models import (
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    Gender,
    InitialRotation,
    Post,
    PostSlot,
    Setting,
    StudyGroup,
    User,
)

from .conftest import INITIAL_ROTATION

SUNDAY = dt.date(2026, 9, 13)
MONDAY, TUESDAY = SUNDAY + dt.timedelta(days=1), SUNDAY + dt.timedelta(days=2)
PASSWORD = "Kuchli-parol-2026"
ILLNESS = "Gripp, yuqori harorat"
pytestmark = pytest.mark.django_db


def at(day: dt.date, hour: int = 20) -> dt.datetime:
    return timezone.make_aware(dt.datetime.combine(day, dt.time(hour, 0)))


@pytest.fixture
def admin(db_cadets, monkeypatch):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    DutyWeek.objects.create(start_date=SUNDAY)
    Setting.load()
    monkeypatch.setattr("django.utils.timezone.now", lambda: at(SUNDAY - dt.timedelta(days=1)))  # shanba kechqurun
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


@pytest.fixture
def admin_client(client, admin):
    client.force_login(admin)
    return client


def boy(group: str, index: int = 0) -> Cadet:
    return Cadet.objects.filter(group__code=group, gender=Gender.MALE, duty_exempt=False, is_active=True).order_by("list_number")[index]


def make_sick(cadet: Cadet, start: dt.date, end: dt.date, admin, illness: str = ILLNESS) -> Absence:
    return Absence.objects.create(cadet=cadet, start_date=start, end_date=end, reason_type="kasal", illness=illness, created_by=admin)


def generate_and_approve(day: dt.date, admin) -> DutyDay:
    draft = services.generate_draft(day, admin)
    return days.approve(day, admin, draft.version)


def on_day(day: dt.date) -> set[int]:
    return set(Assignment.objects.filter(duty_day__date=day).values_list("cadet_id", flat=True))


def login_cadet(client, cadet: Cadet, lang: str = "uz"):
    user = User.objects.create_user(f"k{cadet.pk}", password=PASSWORD, role="cadet", cadet=cadet, language=lang)
    client.force_login(user)
    return client


# ---------------------------------------------------------------------------
# 1. Generator
# ---------------------------------------------------------------------------


def test_sick_cadet_not_picked_inside_period_and_returns_after(admin):
    # Kim yakshanba 1-NO‘J da turishini bilamiz, keyin uni yakshanba–dushanba kasal qilamiz
    probe = services.generate_draft(SUNDAY, admin)
    target = Assignment.objects.get(duty_day=probe, post_slot=PostSlot.objects.get(post__code="noj1", position=1)).cadet
    days.delete_draft(SUNDAY, "sinov", admin, probe.version)
    make_sick(target, SUNDAY, MONDAY, admin)
    # chegaralar: birinchi va oxirgi kun ichida, oldingi va keyingi kun — tashqarida
    ids = lambda day: {a.cadet_id for a in services.engine_absences(day)}
    assert target.pk in ids(SUNDAY) and target.pk in ids(MONDAY)
    assert target.pk not in ids(SUNDAY - dt.timedelta(days=1)) and target.pk not in ids(TUESDAY)

    generate_and_approve(SUNDAY, admin)
    assert target.pk not in on_day(SUNDAY)
    generate_and_approve(MONDAY, admin)
    assert target.pk not in on_day(MONDAY)
    # muddat tugagach oddiy navbatga qaytadi: hafta ichida guruhdagi hamma bir marta turadi
    seen = set()
    for i in range(2, 7):
        day = SUNDAY + dt.timedelta(days=i)
        generate_and_approve(day, admin)
        seen |= on_day(day)
    assert target.pk in seen


def test_extend_and_recover_change_the_result(admin, monkeypatch):
    target = boy("BI-325")
    absence = make_sick(target, SUNDAY, SUNDAY, admin)
    ids = lambda day: {a.cadet_id for a in services.engine_absences(day)}
    assert target.pk not in ids(MONDAY)
    sick_service.extend(absence, TUESDAY + dt.timedelta(days=2), admin)
    assert target.pk in ids(MONDAY) and target.pk in ids(TUESDAY)
    # “Sog‘ayib qaytdi” dushanba sutkasida: muddat dushanba bilan tugaydi, seshanbadan navbatda
    monkeypatch.setattr("django.utils.timezone.now", lambda: at(MONDAY))
    sick_service.recover(absence, admin)
    absence.refresh_from_db()
    assert absence.end_date == MONDAY
    assert target.pk in ids(MONDAY) and target.pk not in ids(TUESDAY)
    actions = list(ChangeLog.objects.filter(cadet=target).values_list("action", flat=True))
    assert "sick_extend" in actions and "sick_recover" in actions


# ---------------------------------------------------------------------------
# 2. Almashtirish oynasi va sutka sahifasi
# ---------------------------------------------------------------------------


def test_replacement_window_excludes_sick_with_reason(admin_client, admin):
    draft = services.generate_draft(SUNDAY, admin)
    slot = PostSlot.objects.get(post__code="noj1", position=1)
    group = INITIAL_ROTATION["noj1"]
    taken = on_day(SUNDAY)
    sick_one = next(c for c in Cadet.objects.filter(group__code=group, gender=Gender.MALE, duty_exempt=False) if c.pk not in taken)
    make_sick(sick_one, SUNDAY, MONDAY, admin)
    candidates = {c.cadet.pk: c for c in days.replacement_candidates(draft, slot)}
    assert candidates[sick_one.pk].excluded.startswith("Kasal: 13.09–14.09")
    body = admin_client.get(reverse("day_replace", args=[SUNDAY.isoformat(), slot.pk]), HTTP_HX_REQUEST="true").content.decode()
    assert "Kasal: 13.09–14.09" in body and ILLNESS not in body  # tavsif oynada ham yo'q
    with pytest.raises(services.ServiceError, match="Kasal"):
        days.replace_cadet(SUNDAY, slot.pk, sick_one.pk, "boshqa", "x", admin, draft.version)


def test_draft_with_sick_cadet_shows_yellow_warning_and_blocks_approval(admin_client, admin):
    draft = services.generate_draft(SUNDAY, admin)
    a = draft.assignments.select_related("cadet").get(post_slot=PostSlot.objects.get(post__code="noj1", position=2))
    response = admin_client.post(reverse("sick_create"), {
        "cadet": a.cadet.pk, "illness": ILLNESS, "start_date": SUNDAY.isoformat(), "end_date": TUESDAY.isoformat(),
    }, follow=True)
    assert "13.09.2026 qoralamasida turibdi" in response.content.decode()
    body = admin_client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()
    assert 'data-testid="sick-issues"' in body and "kasallar ro‘yxatida (13.09–15.09)" in body
    assert reverse("day_replace", args=[SUNDAY.isoformat(), a.post_slot_id]) in body  # “Almashtirish” tugmasi
    with pytest.raises(services.ServiceError, match="Tasdiqlab bo‘lmaydi"):
        days.approve(SUNDAY, admin, draft.version)


def test_sick_on_approved_day_keeps_roster_and_warns(admin_client, admin):
    day = generate_and_approve(SUNDAY, admin)
    before = list(day.assignments.order_by("post_slot_id").values_list("post_slot_id", "cadet_id"))
    a = day.assignments.select_related("cadet").first()
    response = admin_client.post(reverse("sick_create"), {
        "cadet": a.cadet.pk, "illness": ILLNESS, "start_date": SUNDAY.isoformat(), "end_date": MONDAY.isoformat(),
    }, follow=True)
    text = f"{a.cadet.short_name} 13.09.2026 sutkada naryadda, u tasdiqlangan. Almashtirish uchun avval tasdiqni bekor qiling."
    assert text in response.content.decode()
    day.refresh_from_db()
    assert day.is_approved and list(day.assignments.order_by("post_slot_id").values_list("post_slot_id", "cadet_id")) == before
    assert text in admin_client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()


# ---------------------------------------------------------------------------
# 3. Kim nimani ko'radi
# ---------------------------------------------------------------------------


def test_cadet_sees_only_dates_others_see_nothing(client, admin):
    day = generate_and_approve(SUNDAY, admin)
    a = day.assignments.select_related("cadet").first()
    make_sick(a.cadet, SUNDAY - dt.timedelta(days=1), SUNDAY + dt.timedelta(days=4), admin)  # 12.09–17.09
    login_cadet(client, a.cadet)
    home = client.get(reverse("home")).content.decode()
    assert "Siz kasallar ro‘yxatidasiz: 12.09 dan 17.09 gacha" in home and 'data-testid="sick-card"' in home
    assert ILLNESS not in home and 'data-testid="duty-post"' not in home  # kartochka o'rnida faqat sanalar
    for name, args in [("my_card", []), ("approved_days", []), ("day_detail", [SUNDAY.isoformat()])]:
        assert ILLNESS not in client.get(reverse(name, args=args), follow=True).content.decode(), name

    other = Cadet.objects.exclude(pk=a.cadet_id).filter(gender=Gender.MALE).first()
    other_client = login_cadet(client.__class__(), other)
    for name, args in [("home", []), ("approved_days", []), ("day_detail", [SUNDAY.isoformat()])]:
        html = other_client.get(reverse(name, args=args)).content.decode()
        assert ILLNESS not in html and "kasallar ro‘yxati" not in html.lower() and 'data-testid="sick' not in html, name
    pdf = other_client.get(reverse("day_pdf", args=[SUNDAY.isoformat()]))
    text = "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages).lower()
    assert "kasal" not in text and a.cadet.last_name.lower() in text  # ro'yxat o'zgarmagan, belgi yo'q


@pytest.mark.parametrize("name", ["sick_list", "sick_create"])
def test_cadet_gets_403_on_sick_pages(client, admin, name):
    absence = make_sick(boy("BI-225"), SUNDAY, MONDAY, admin)
    login_cadet(client, absence.cadet)
    assert client.get(reverse(name)).status_code == 403
    assert client.get(reverse("sick_edit", args=[absence.pk])).status_code == 403
    for post_name in ("sick_edit", "sick_extend", "sick_recover", "sick_delete"):
        assert client.post(reverse(post_name, args=[absence.pk]), {"end_date": "2026-09-30", "illness": "x"}).status_code == 403
    assert client.post(reverse("sick_create"), {"cadet": absence.cadet.pk, "illness": "x"}).status_code == 403
    absence.refresh_from_db()
    assert absence.end_date == MONDAY and absence.illness == ILLNESS


# ---------------------------------------------------------------------------
# 4. Sahifa: qo'shish, tahrirlash, filtr, jurnal, uch til
# ---------------------------------------------------------------------------


def test_add_edit_extend_recover_delete_with_log(client, admin, monkeypatch):
    monkeypatch.setattr("django.utils.timezone.now", lambda: at(dt.date(2026, 9, 15)))  # 15.09 sutkasi
    admin_client = client
    admin_client.force_login(admin)
    cadet = boy("BI-425")
    data = {"cadet": cadet.pk, "illness": "", "start_date": "2026-09-14", "end_date": "2026-09-13"}
    body = admin_client.post(reverse("sick_create"), data).content.decode()
    assert "Ushbu maydon to‘ldirilishi shart." in body  # tavsif majburiy
    assert "Oxirgi sutka birinchisidan oldin bo‘lishi mumkin emas." in admin_client.post(
        reverse("sick_create"), {**data, "illness": ILLNESS}).content.decode()
    assert admin_client.post(reverse("sick_create"), {**data, "illness": ILLNESS, "end_date": "2026-09-16"}).status_code == 302
    absence = Absence.objects.get(cadet=cadet)
    assert absence.reason_type == "kasal" and absence.illness == ILLNESS and absence.created_by == admin
    # ustma-ust yozuv kiritilmaydi
    assert "allaqachon yozuv bor" in admin_client.post(
        reverse("sick_create"), {**data, "illness": "x", "start_date": "2026-09-15", "end_date": "2026-09-20"}).content.decode()

    admin_client.post(reverse("sick_edit", args=[absence.pk]), {"illness": "Angina", "start_date": "2026-09-14", "end_date": "2026-09-17"})
    absence.refresh_from_db()
    assert absence.illness == "Angina" and absence.end_date == dt.date(2026, 9, 17)
    admin_client.post(reverse("sick_extend", args=[absence.pk]), {"end_date": "2026-09-16"})  # qisqartirib bo'lmaydi
    absence.refresh_from_db()
    assert absence.end_date == dt.date(2026, 9, 17)
    admin_client.post(reverse("sick_extend", args=[absence.pk]), {"end_date": "2026-09-19"})
    absence.refresh_from_db()
    assert absence.end_date == dt.date(2026, 9, 19)
    admin_client.post(reverse("sick_recover", args=[absence.pk]))
    absence.refresh_from_db()
    assert absence.end_date == dt.date(2026, 9, 15)
    admin_client.post(reverse("sick_delete", args=[absence.pk]))  # boshlangan — o'chirilmaydi
    assert Absence.objects.filter(pk=absence.pk).exists()

    future = make_sick(boy("BI-525"), dt.date(2026, 9, 20), dt.date(2026, 9, 22), admin)
    admin_client.post(reverse("sick_delete", args=[future.pk]))
    assert not Absence.objects.filter(pk=future.pk).exists()
    actions = list(ChangeLog.objects.filter(action__startswith="sick_").values_list("action", flat=True))
    assert sorted(set(actions)) == ["sick_add", "sick_delete", "sick_edit", "sick_extend", "sick_recover"]
    assert ChangeLog.objects.filter(action="sick_add", cadet=cadet, user=admin, details__contains=ILLNESS).exists()


def test_started_record_keeps_start_date(admin_client, admin, monkeypatch):
    absence = make_sick(boy("BI-625"), SUNDAY - dt.timedelta(days=2), SUNDAY, admin)
    admin_client.post(reverse("sick_edit", args=[absence.pk]), {"illness": "x", "start_date": "2026-09-01", "end_date": "2026-09-13"})
    absence.refresh_from_db()
    assert absence.start_date == SUNDAY - dt.timedelta(days=2) and absence.illness == "x"


def test_list_filters_and_columns(admin_client, admin):
    now = make_sick(boy("BI-225"), SUNDAY - dt.timedelta(days=3), SUNDAY + dt.timedelta(days=2), admin)
    done = make_sick(boy("BI-325"), dt.date(2026, 9, 1), dt.date(2026, 9, 3), admin, illness="Shamollash")
    future = make_sick(boy("BI-425"), SUNDAY + dt.timedelta(days=3), SUNDAY + dt.timedelta(days=5), admin, illness="Operatsiya")
    body = admin_client.get(reverse("sick_list")).content.decode()
    assert f'data-testid="sick-{now.pk}"' in body and f'data-testid="sick-{done.pk}"' not in body
    assert ILLNESS in body and "10.09.2026" in body and "15.09.2026" in body and "davom etmoqda" in body and "kursboshligi" in body
    body = admin_client.get(reverse("sick_list"), {"holat": "hammasi"}).content.decode()
    for a in (now, done, future):
        assert f'data-testid="sick-{a.pk}"' in body
    assert "tugagan" in body and "kelajakda" in body
    body = admin_client.get(reverse("sick_list"), {"holat": "hammasi", "guruh": "BI-325"}).content.decode()
    assert f'data-testid="sick-{done.pk}"' in body and f'data-testid="sick-{now.pk}"' not in body
    # “Sababli holatlar” sahifasida ham ko'rinadi, tahrirlash havolasi bilan
    absences = admin_client.get(reverse("absence_list")).content.decode()
    assert now.cadet.short_name in absences and reverse("sick_edit", args=[now.pk]) in absences


@pytest.mark.parametrize("lang, title", [("uz", "Kasallar ro‘yxati"), ("ru", "Список больных"), ("en", "Sick list")])
def test_pages_open_in_three_languages(client, admin, lang, title):
    absence = make_sick(boy("BI-225"), SUNDAY, MONDAY, admin)
    admin.language = lang
    admin.save()
    client.force_login(admin)
    for name, args in [("sick_list", []), ("sick_create", []), ("sick_edit", [absence.pk])]:
        response = client.get(reverse(name, args=args))
        assert response.status_code == 200, (lang, name)
    assert title in client.get(reverse("sick_list")).content.decode()
    extend = {"uz": "Muddatni uzaytirish", "ru": "Продлить срок", "en": "Extend period"}[lang]
    recovered = {"uz": "Sog‘ayib qaytdi", "ru": "Выздоровел", "en": "Recovered"}[lang]
    page = client.get(reverse("sick_edit", args=[absence.pk])).content.decode()
    assert extend in page and recovered in page


def test_menu_has_sick_list_for_admin_only(client, admin):
    client.force_login(admin)
    assert reverse("sick_list") in client.get(reverse("home")).content.decode()
    login_cadet(client, boy("BI-225"))
    assert reverse("sick_list") not in client.get(reverse("home")).content.decode()


def test_sick_offender_gets_notice_and_waits(admin):
    offender = boy(INITIAL_ROTATION["markaz"])
    penalties.add(offender, "tartib", "x", SUNDAY - dt.timedelta(days=1), 1, admin)  # tanbeh kelajakda bo‘lmaydi (soat shanbada)
    make_sick(offender, SUNDAY, SUNDAY, admin)
    draft = services.generate_draft(SUNDAY, admin)
    assert offender.pk not in on_day(SUNDAY)
    assert any("sababli holatda" in n for n in days.penalty_notices(draft))
