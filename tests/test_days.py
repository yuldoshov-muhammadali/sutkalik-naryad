"""7-bosqich: haftalar, sutka (tuzish → tuzatish → tasdiqlash), sababli holatlar, jurnal."""

from __future__ import annotations

import datetime as dt

import pytest
from django.urls import reverse

from naryad import days, services
from naryad.models import (
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    InitialRotation,
    Post,
    PostSlot,
    StudyGroup,
    User,
)

from .conftest import INITIAL_ROTATION

SUNDAY = dt.date(2026, 9, 13)
MONDAY = SUNDAY + dt.timedelta(days=1)
PASSWORD = "Kuchli-parol-2026"
pytestmark = pytest.mark.django_db


@pytest.fixture
def admin(db_cadets):
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


@pytest.fixture
def admin_client(client, admin):
    client.force_login(admin)
    return client


@pytest.fixture
def rotation(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))


@pytest.fixture
def week(rotation):
    return DutyWeek.objects.create(start_date=SUNDAY)


@pytest.fixture
def draft(week, admin):
    return services.generate_draft(SUNDAY, admin)


def url(name, *args):
    return reverse(name, args=[a.isoformat() if isinstance(a, dt.date) else a for a in args])


def slot(post_code, position=1) -> PostSlot:
    return PostSlot.objects.get(post__code=post_code, position=position)


def assigned(day: DutyDay, post_code, position=1) -> Assignment:
    return Assignment.objects.get(duty_day=day, post_slot=slot(post_code, position))


def best_candidate(day: DutyDay, s: PostSlot) -> Cadet:
    return next(c.cadet for c in days.replacement_candidates(day, s) if not c.excluded)


def approve(client, date):
    day = DutyDay.objects.get(date=date)
    return client.post(url("day_approve", date), {"version": day.version})


# ---------------------------------------------------------------------------
# To'liq oqim
# ---------------------------------------------------------------------------


def test_full_flow_open_generate_replace_approve_next_day(admin_client, rotation):
    # 1) haftani ochish
    resp = admin_client.post(reverse("week_open"), {"start_date": SUNDAY.isoformat()})
    assert resp.status_code == 302 and DutyWeek.objects.filter(start_date=SUNDAY).exists()

    # 2) sutka sahifasi — "Tuzish"
    body = admin_client.get(url("day_detail", SUNDAY)).content.decode()
    assert "Tuzish" in body and "Tuzilmagan" in body
    admin_client.post(url("day_generate", SUNDAY), {"version": 0})
    day = DutyDay.objects.get(date=SUNDAY)
    assert day.status == "draft" and day.assignments.count() == 20

    # 3) rasmiy shaklga o'xshash ko'rinish
    body = admin_client.get(url("day_detail", SUNDAY)).content.decode()
    for title in ["Markaz bo‘yicha", "1-NO‘J bo‘yicha", "2-NO‘J bo‘yicha", "1-Yotoqxona bo‘yicha",
                  "O‘quv binosi bo‘yicha", "Institut bo‘yicha patrul", "Qizlar yotoqxonasi bo‘yicha"]:
        assert title in body
    assert "BI-525 guruhi" in body and "qizlar navbati" in body

    # 4) almashtirish (kasal) → Absence va jurnal
    s = slot("noj1", 1)
    old = assigned(day, "noj1").cadet
    new = best_candidate(day, s)
    resp = admin_client.post(
        url("day_replace", SUNDAY, s.pk), {"cadet": new.pk, "reason": "kasal", "note": "ma’lumotnoma", "version": day.version}
    )
    assert resp.status_code == 302
    assert assigned(day, "noj1").cadet == new
    assert Absence.objects.filter(cadet=old, start_date=SUNDAY, end_date=SUNDAY, reason_type="kasal").exists()
    log = ChangeLog.objects.get(duty_day=day, action="replace")
    assert (log.old_cadet, log.new_cadet, log.reason, log.post_slot) == (old, new, "Kasal: ma’lumotnoma", s)

    # 5) tasdiqlash
    assert approve(admin_client, SUNDAY).status_code == 302
    day.refresh_from_db()
    assert day.status == "approved" and day.approved_by is not None

    # 6) keyingi sutka tarixni hisobga oladi
    admin_client.post(url("day_generate", MONDAY), {"version": 0})
    nxt = DutyDay.objects.get(date=MONDAY)
    today_ids = set(nxt.assignments.values_list("cadet_id", flat=True))
    assert new.pk not in today_ids  # kecha (almashtirib qo'yilgan) turgan — bugun olinmaydi
    assert {g.post.code: g.group.code for g in nxt.group_posts.all()}["noj2"] == INITIAL_ROTATION["noj1"]
    history_ids = {r.cadet_id for r in services.approved_history()}
    assert new.pk in history_ids and old.pk not in {r.cadet_id for r in services.approved_history() if r.post == "noj1"}


def test_regenerate_replaces_draft_and_logs(admin_client, draft):
    v = draft.version
    admin_client.post(url("day_generate", SUNDAY), {"version": v})
    draft.refresh_from_db()
    assert draft.version == v + 1
    log = ChangeLog.objects.filter(duty_day=draft, action="generate").order_by("-id").first()
    assert "Qayta tuzildi" in log.details


# ---------------------------------------------------------------------------
# Taqiqlangan almashtirishlar
# ---------------------------------------------------------------------------


def try_replace(day, s, cadet, reason="sababli", note=""):
    with pytest.raises(services.ServiceError) as exc:
        days.replace_cadet(day.date, s.pk, cadet.pk, reason, note, None, day.version)
    return str(exc.value)


def test_forbidden_replacements(draft, admin):
    s = slot("noj1", 1)
    before = assigned(draft, "noj1").cadet_id
    other_group = Cadet.objects.filter(gender="M", duty_exempt=False).exclude(group__code=INITIAL_ROTATION["noj1"]).first()
    girl = Cadet.objects.filter(gender="F").first()
    boy = Cadet.objects.filter(gender="M", duty_exempt=False, group__code=INITIAL_ROTATION["noj1"]).exclude(
        pk__in=draft.assignments.values("cadet_id")
    ).first()

    assert "boshqa guruhdan" in try_replace(draft, s, other_group)
    assert "Qizlar faqat Qizlar yotoqxonasida" in try_replace(draft, s, girl)
    assert "O‘g‘il bolani Qizlar yotoqxonasiga" in try_replace(draft, slot("qizlar", 1), boy)
    same_day = assigned(draft, "noj1", 2).cadet
    assert "shu sutkada boshqa o‘rinda turibdi" in try_replace(draft, s, same_day)

    boy.is_active, boy.deactivation_reason = False, "test"
    boy.save()
    assert "faol emas" in try_replace(draft, s, boy)
    boy.is_active = True
    boy.save()
    Absence.objects.create(cadet=boy, start_date=SUNDAY, end_date=SUNDAY, reason_type="tatil")
    assert "sababli yo‘q" in try_replace(draft, s, boy)
    assert assigned(draft, "noj1").cadet_id == before  # hech narsa o'zgarmadi


def test_yesterday_duty_is_forbidden(admin_client, draft, admin):
    days.approve(SUNDAY, admin, draft.version)
    nxt = services.generate_draft(MONDAY, admin)
    yesterday_cadet = Assignment.objects.get(duty_day=draft, post_slot=slot("noj1", 1)).cadet
    # 1-NO'J dagi guruh bugun 2-NO'J da — o'sha guruhdan kecha turgan kursantni qo'yishga urinamiz
    s = slot("noj2", 1)
    msg = try_replace(nxt, s, yesterday_cadet)
    assert "kecha (13.09) naryadda bo‘lgan" in msg


def test_forbidden_replacement_message_shown_in_modal(admin_client, draft):
    s = slot("noj1", 1)
    girl = Cadet.objects.filter(gender="F").first()
    resp = admin_client.post(
        url("day_replace", SUNDAY, s.pk), {"cadet": girl.pk, "reason": "sababli", "version": draft.version},
        HTTP_HX_REQUEST="true",
    )
    assert resp.status_code == 200 and "Qizlar faqat Qizlar yotoqxonasida" in resp.content.decode()


def test_replacement_requires_reason(draft):
    s = slot("noj1", 1)
    new = best_candidate(draft, s)
    with pytest.raises(services.ServiceError, match="Sabab tanlanmagan"):
        days.replace_cadet(SUNDAY, s.pk, new.pk, "", "", None, draft.version)
    with pytest.raises(services.ServiceError, match="izoh majburiy"):
        days.replace_cadet(SUNDAY, s.pk, new.pk, "boshqa", "  ", None, draft.version)
    assert not ChangeLog.objects.filter(action="replace").exists()


def test_candidates_sorted_best_first_with_stats(admin_client, draft):
    s = slot("noj1", 1)
    cands = days.replacement_candidates(draft, s)
    eligible = [c for c in cands if not c.excluded]
    assert eligible[0].best and all(c.week_count is not None for c in eligible)
    excluded = {c.cadet.pk: c.excluded for c in cands if c.excluded}
    # shu sutkada boshqa o'rinda turganlar chiqarilgan
    assert excluded[assigned(draft, "noj1", 2).cadet_id] == "bugun boshqa o‘ringa qo‘yilgan"
    body = admin_client.get(url("day_replace", SUNDAY, s.pk), HTTP_HX_REQUEST="true").content.decode()
    assert "eng munosib" in body and "haftada:" in body and "<html" not in body


def test_absence_created_only_for_sick_and_leave(draft):
    for pos, reason, expect in [(1, "tatil", True), (2, "sababli", False)]:
        d = DutyDay.objects.get(pk=draft.pk)
        s = slot("noj1", pos)
        old = assigned(d, "noj1", pos).cadet
        days.replace_cadet(SUNDAY, s.pk, best_candidate(d, s).pk, reason, "", None, d.version)
        assert Absence.objects.filter(cadet=old, start_date=SUNDAY).exists() is expect


# ---------------------------------------------------------------------------
# Lavozimlarni almashtirish
# ---------------------------------------------------------------------------


def test_swap_roles_within_post(admin_client, draft):
    a, b = assigned(draft, "noj1", 1).cadet, assigned(draft, "noj1", 3).cadet
    resp = admin_client.post(
        url("day_swap", SUNDAY, Post.objects.get(code="noj1").pk),
        {"slot_a": slot("noj1", 1).pk, "slot_b": slot("noj1", 3).pk, "reason": "sababli", "note": "", "version": draft.version},
    )
    assert resp.status_code == 302
    assert assigned(draft, "noj1", 1).cadet == b and assigned(draft, "noj1", 3).cadet == a
    log = ChangeLog.objects.get(duty_day=draft, action="swap")
    assert "Navbatchi → Posbon" in log.details


def test_swap_rules(draft):
    with pytest.raises(services.ServiceError, match="bitta joy ichida"):
        days.swap_slots(SUNDAY, slot("noj1", 1).pk, slot("noj2", 1).pk, "sababli", "", None, draft.version)
    with pytest.raises(services.ServiceError, match="lavozim bir xil"):
        days.swap_slots(SUNDAY, slot("noj1", 3).pk, slot("noj1", 4).pk, "sababli", "", None, draft.version)


# ---------------------------------------------------------------------------
# Tasdiqlash va bekor qilish
# ---------------------------------------------------------------------------


def test_cadet_cannot_approve_or_see_draft(client, draft):
    cadet_user = User.objects.create_user("k", password=PASSWORD, role="cadet", cadet=Cadet.objects.first())
    client.force_login(cadet_user)
    assert client.post(url("day_approve", SUNDAY), {"version": draft.version}).status_code == 403
    assert client.get(url("day_detail", SUNDAY)).status_code == 403  # sutka sahifalari kursantga yopiq (14-bosqich)
    for name, args in [("week_list", []), ("absence_list", []), ("day_log", [SUNDAY]), ("day_replace", [SUNDAY, slot("noj1").pk])]:
        assert client.get(url(name, *args)).status_code == 403
    draft.refresh_from_db()
    assert draft.status == "draft"


def test_cadet_sees_approved_day_pages_read_only(client, draft, admin):
    """16-bosqich: kursant tasdiqlangan sutkani faqat o'qish uchun ko'radi; qoralama — 403 (CLAUDE.md 63-band)."""
    cadet_user = User.objects.create_user("k", password=PASSWORD, role="cadet", cadet=Cadet.objects.first())
    client.force_login(cadet_user)
    assert client.get(url("day_detail", SUNDAY)).status_code == 403  # hali qoralama
    days.approve(SUNDAY, admin, draft.version)
    body = client.get(url("day_detail", SUNDAY)).content.decode()
    assert "Almashtirish" not in body and "Tasdiqni bekor qilish" not in body and "Jurnal" not in body
    assert "13-sentabr" in client.get(reverse("approved_days")).content.decode()
    client.force_login(admin)
    assert "13-sentabr" in client.get(reverse("approved_days")).content.decode()


def test_cannot_approve_with_empty_slot(admin_client, draft):
    Assignment.objects.filter(duty_day=draft, post_slot=slot("patrul", 4)).delete()
    body = admin_client.get(url("day_detail", SUNDAY)).content.decode()
    assert "Institut bo‘yicha patrul: 1 ta o‘rin bo‘sh" in body and "— bo‘sh —" in body
    resp = approve(admin_client, SUNDAY)
    draft.refresh_from_db()
    assert draft.status == "draft"
    assert "Tasdiqlab bo‘lmaydi" in admin_client.get(resp["Location"]).content.decode()
    # bo'sh o'rinni to'ldirib, keyin tasdiqlash mumkin
    s = slot("patrul", 4)
    days.replace_cadet(SUNDAY, s.pk, best_candidate(draft, s).pk, "boshqa", "bo‘sh o‘rin", None, draft.version)
    assert approve(admin_client, SUNDAY).status_code == 302
    draft.refresh_from_db()
    assert draft.status == "approved"


def test_cannot_approve_with_inactive_cadet(draft, admin):
    c = assigned(draft, "markaz").cadet
    c.is_active, c.deactivation_reason = False, "test"
    c.save()
    draft.refresh_from_db()
    assert any(i.kind == "inactive" for i in days.day_issues(draft))
    with pytest.raises(services.ServiceError, match="faol emas"):
        days.approve(SUNDAY, admin, draft.version)


def test_reopen_rules(admin_client, draft, admin):
    days.approve(SUNDAY, admin, draft.version)
    draft.refresh_from_db()
    # sababsiz — rad etiladi
    with pytest.raises(services.ServiceError, match="sababi majburiy"):
        days.reopen(SUNDAY, "  ", admin, draft.version)
    # keyingi sutka tuzilmagan — mumkin
    resp = admin_client.post(url("day_reopen", SUNDAY), {"reason": "xato kiritilgan", "version": draft.version})
    assert resp.status_code == 302
    draft.refresh_from_db()
    assert draft.status == "draft" and ChangeLog.objects.filter(duty_day=draft, action="reopen", reason="xato kiritilgan").exists()

    # qayta tasdiqlab, keyingi sutkani tuzamiz — endi bekor qilib bo'lmaydi
    days.approve(SUNDAY, admin, draft.version)
    services.generate_draft(MONDAY, admin)
    draft.refresh_from_db()
    with pytest.raises(services.ServiceError, match="Keyingi sutka"):
        days.reopen(SUNDAY, "sabab", admin, draft.version)
    assert "allaqachon tuzilgan" in admin_client.get(url("day_detail", SUNDAY)).content.decode()


def test_approved_day_is_read_only(draft, admin):
    days.approve(SUNDAY, admin, draft.version)
    draft.refresh_from_db()
    s = slot("noj1", 1)
    with pytest.raises(services.ServiceError, match="tasdiqlangan"):
        days.replace_cadet(SUNDAY, s.pk, Cadet.objects.first().pk, "sababli", "", admin, draft.version)
    with pytest.raises(services.ServiceError, match="allaqachon tasdiqlangan"):
        services.generate_draft(SUNDAY, admin)


# ---------------------------------------------------------------------------
# Bir vaqtda ishlash (versiya)
# ---------------------------------------------------------------------------


def test_stale_version_is_rejected(admin_client, draft):
    old_version = draft.version
    s = slot("noj1", 1)
    days.replace_cadet(SUNDAY, s.pk, best_candidate(draft, s).pk, "sababli", "", None, old_version)  # 1-foydalanuvchi
    draft.refresh_from_db()
    before = assigned(draft, "noj1").cadet_id
    s2 = slot("noj1", 2)
    with pytest.raises(services.StaleError):
        days.replace_cadet(SUNDAY, s2.pk, best_candidate(draft, s2).pk, "sababli", "", None, old_version)  # 2-foydalanuvchi
    resp = admin_client.post(
        url("day_replace", SUNDAY, s2.pk), {"cadet": best_candidate(draft, s2).pk, "reason": "sababli", "version": old_version},
        HTTP_HX_REQUEST="true",
    )
    assert "sahifani yangilang" in resp.content.decode()
    assert assigned(draft, "noj1").cadet_id == before
    resp = admin_client.post(url("day_approve", SUNDAY), {"version": old_version}, follow=True)
    assert "sahifani yangilang" in resp.content.decode()


def test_double_generate_is_rejected(admin_client, week, admin):
    services.generate_draft(SUNDAY, admin, expected_version=0)
    with pytest.raises(services.StaleError):
        services.generate_draft(SUNDAY, admin, expected_version=0)  # ikkinchi "Tuzish" bosilgan
    resp = admin_client.post(url("day_generate", SUNDAY), {"version": 0}, follow=True)
    assert "sahifani yangilang" in resp.content.decode()
    assert DutyDay.objects.get(date=SUNDAY).version == 1


# ---------------------------------------------------------------------------
# Haftalar sahifasi
# ---------------------------------------------------------------------------


def test_weeks_page_open_and_validation(admin_client):
    body = admin_client.get(reverse("week_list")).content.decode()
    assert "boshlang‘ich guruh → joy taqsimoti ham yo‘q" in body and reverse("admin:naryad_setting_change", args=[1]) in body
    resp = admin_client.post(reverse("week_open"), {"start_date": MONDAY.isoformat()}, follow=True)
    assert "yakshanba" in resp.content.decode() and not DutyWeek.objects.exists()
    admin_client.post(reverse("week_open"), {"start_date": SUNDAY.isoformat()})
    body = admin_client.get(reverse("week_list")).content.decode()
    assert "13.09.2026" in body and body.count("Tuzilmagan") == 7
    resp = admin_client.post(reverse("week_open"), {"start_date": SUNDAY.isoformat()}, follow=True)
    assert "Hafta ochilmadi" in resp.content.decode()


def test_week_preview(admin_client):
    body = admin_client.get(reverse("week_preview"), {"start_date": SUNDAY.isoformat()}).content.decode()
    assert "7-sutka" in body and "13-sentabr 18:00 → 14-sentabr 18:00" in body
    body = admin_client.get(reverse("week_preview"), {"start_date": MONDAY.isoformat()}).content.decode()
    assert "yakshanba emas" in body


def test_day_outside_week_redirects(admin_client, rotation):
    resp = admin_client.get(url("day_detail", SUNDAY))
    assert resp.status_code == 302 and resp["Location"] == reverse("week_list")


# ---------------------------------------------------------------------------
# Sababli holatlar sahifasi
# ---------------------------------------------------------------------------


def test_absence_page_add_overlap_change_delete(admin_client, monkeypatch):
    monkeypatch.setattr("naryad.absences.current_duty_date", lambda: SUNDAY)
    monkeypatch.setattr("naryad.views_days.current_duty_date", lambda: SUNDAY)
    cadet = Cadet.objects.get(last_name="Maxsudov")
    data = {"cadet": cadet.pk, "reason_type": "kasal", "start_date": "2026-09-12", "end_date": "2026-09-14", "note": ""}
    assert admin_client.post(reverse("absence_list"), data).status_code == 302
    started = Absence.objects.get(cadet=cadet)
    # ustma-ust tushadigan yozuv rad etiladi
    data2 = {**data, "start_date": "2026-09-14", "end_date": "2026-09-16"}
    body = admin_client.post(reverse("absence_list"), data2).content.decode()
    assert "allaqachon yozuv bor" in body and Absence.objects.count() == 1
    # "boshqa" — izohsiz bo'lmaydi
    body = admin_client.post(reverse("absence_list"), {**data, "start_date": "2026-09-20", "end_date": "2026-09-20", "reason_type": "boshqa"}).content.decode()
    assert "izoh majburiy" in body
    # boshlangan yozuv: o'chirib bo'lmaydi, tugash sanasini o'zgartirish mumkin
    assert admin_client.post(reverse("absence_delete", args=[started.pk])).status_code == 403
    admin_client.post(reverse("absence_end", args=[started.pk]), {"end_date": "2026-09-13"})
    started.refresh_from_db()
    assert started.end_date == SUNDAY
    assert ChangeLog.objects.filter(cadet=cadet, action="absence_change").exists()
    # kelgusi yozuvni o'chirish mumkin
    admin_client.post(reverse("absence_list"), {**data, "start_date": "2026-09-20", "end_date": "2026-09-21", "reason_type": "sababli"})
    future = Absence.objects.get(cadet=cadet, start_date=dt.date(2026, 9, 20))
    assert admin_client.post(reverse("absence_delete", args=[future.pk])).status_code == 302
    assert not Absence.objects.filter(pk=future.pk).exists()
    body = admin_client.get(reverse("absence_list")).content.decode()
    assert "Hozir band (1)" in body and "Maxsudov H" in body


def test_absent_cadet_excluded_from_generation(week, admin):
    target = Cadet.objects.filter(group__code=INITIAL_ROTATION["noj1"], gender="M").first()
    Absence.objects.create(cadet=target, start_date=SUNDAY, end_date=SUNDAY + dt.timedelta(days=3), reason_type="sababli")
    day = services.generate_draft(SUNDAY, admin)
    assert target.pk not in set(day.assignments.values_list("cadet_id", flat=True))


# ---------------------------------------------------------------------------
# Jurnal
# ---------------------------------------------------------------------------


def test_day_log_in_time_order(admin_client, draft, admin):
    s = slot("noj1", 1)
    days.replace_cadet(SUNDAY, s.pk, best_candidate(draft, s).pk, "sababli", "test", admin, draft.version)
    draft.refresh_from_db()
    days.approve(SUNDAY, admin, draft.version)
    body = admin_client.get(url("day_log", SUNDAY)).content.decode()
    i_gen, i_rep, i_app = body.index("Qoralama tuzildi"), body.index("Almashtirildi"), body.index("Tasdiqlandi")
    assert i_gen < i_rep < i_app
    assert "Sabab: Sababli: test" in body
