"""Naryaddan ozod kursantlar (komandirlar va kurs lavozimlari) — CLAUDE.md 2-, 4-bo'lim, 10-bo'lim 56-band."""

from __future__ import annotations

import datetime as dt
import importlib
from collections import Counter

import pytest
from django.apps import apps as django_apps
from django.urls import reverse

from naryad import cadets as cadet_service, days, services, stats
from naryad.importers import EXPECTED_ON_DUTY, load_roster
from naryad.models import (
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    Gender,
    InitialRotation,
    Post,
    PostSlot,
    StudyGroup,
    User,
)
from naryad.services import ServiceError

from .conftest import INITIAL_ROTATION

PASSWORD = "Kuchli-parol-2026"
SUNDAY = dt.date(2026, 9, 13)
pytestmark = pytest.mark.django_db

EXEMPT_NAMES = {
    ("YuP-125", "Abduqodirov Abdulqosim Abdulxakim o‘g‘li"): "Kurs starshinasi",
    ("YuP-125", "Tojiyev Sherali Tolmas o‘g‘li"): "YuP-125 guruh komandiri",
    ("BI-225", "Eshmatov Jobirbek Baxtiyor o‘g‘li"): "BI-225 guruh komandiri",
    ("BI-225", "Bo‘riyev Shohruxmirzo Norbobo o‘g‘li"): "Kurs pisari",
    ("BI-325", "Akramjonov Axmadjon Akramjon o‘g‘li"): "BI-325 guruh komandiri",
    ("BI-325", "Xayrillayev Javohir Oybek o‘g‘li"): "Kaptyorchik",
    ("BI-425", "Navro‘zov Jasurbek Baxtiyor o‘g‘li"): "BI-425 guruh komandiri",
    ("BI-525", "Abdulazizov Oyatillo Abduxalilovich"): "BI-525 guruh komandiri",
    ("BI-625", "O‘rmonjonov Muxammadqodir Jaxongir o‘g‘li"): "BI-625 guruh komandiri",
}


@pytest.fixture
def admin(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


def exempt_set() -> dict[tuple[str, str], str]:
    return {(c.group.code, c.full_name): c.duty_position for c in Cadet.objects.filter(duty_exempt=True).select_related("group")}


def open_weeks(start: dt.date, count: int, admin, step_days: int = 7):
    for i in range(count):
        DutyWeek.objects.get_or_create(start_date=start + dt.timedelta(days=step_days * i), defaults={"created_by": admin})


def generate_and_approve(date: dt.date, admin) -> DutyDay:
    day = services.generate_draft(date, admin)
    return days.approve(date, admin, day.version)


# ---------------------------------------------------------------------------
# Ma'lumot: migratsiya va load_roster
# ---------------------------------------------------------------------------


def run_migration_function():
    module = importlib.import_module("naryad.migrations.0010_cadet_duty_exempt")
    module.mark_exempt(django_apps, None)


def test_migration_marks_exactly_nine(db_cadets):
    Cadet.objects.update(duty_exempt=False, duty_position="")
    run_migration_function()
    assert exempt_set() == EXEMPT_NAMES
    logs = ChangeLog.objects.filter(action=ChangeLog.Action.CADET_EXEMPT)
    assert logs.count() == 9 and all(log.reason and log.user is None for log in logs)
    run_migration_function()  # qayta ishga tushirilsa — ikki marta yozilmaydi
    assert ChangeLog.objects.filter(action=ChangeLog.Action.CADET_EXEMPT).count() == 9


def test_migration_stops_when_name_not_found(db_cadets):
    Cadet.objects.update(duty_exempt=False, duty_position="")
    c = Cadet.objects.get(last_name="Navro‘zov")
    c.first_name = "Jasur"
    c.save()
    with pytest.raises(RuntimeError, match="Navro‘zov Jasurbek Baxtiyor o‘g‘li: 0 ta mos"):
        run_migration_function()


def test_migration_is_noop_on_empty_database(db):
    run_migration_function()
    assert not Cadet.objects.exists()


def test_load_roster_reads_exempt_flag_and_counts(db):
    report = load_roster()
    assert exempt_set() == EXEMPT_NAMES
    assert report.on_duty == EXPECTED_ON_DUTY and sum(report.on_duty.values()) == 78
    assert len(report.exempt) == 9 and not report.warnings
    assert ChangeLog.objects.filter(action=ChangeLog.Action.CADET_EXEMPT).count() == 9
    assert Cadet.objects.filter(gender=Gender.FEMALE, duty_exempt=False).count() == 13
    # admin olib tashlasa va load_roster qayta ishlasa — roster.json holatiga qaytadi va jurnalga yoziladi
    c = Cadet.objects.get(last_name="Tojiyev", first_name="Sherali")
    cadet_service.clear_exempt(c, "sinov", None)
    load_roster()
    c.refresh_from_db()
    assert c.duty_exempt and c.duty_position == "YuP-125 guruh komandiri"


def test_exempt_requires_position_constraint(db_cadets):
    from django.db import IntegrityError, transaction

    c = Cadet.objects.filter(duty_exempt=False, gender=Gender.MALE).first()
    c.duty_exempt = True
    with pytest.raises(IntegrityError), transaction.atomic():
        c.save()


# ---------------------------------------------------------------------------
# Generator: 12 haftalik simulyatsiya, eng kichik guruh
# ---------------------------------------------------------------------------


def test_generator_never_picks_exempt_in_12_weeks(admin):
    exempt_ids = set(Cadet.objects.filter(duty_exempt=True).values_list("pk", flat=True))
    starts = [SUNDAY + dt.timedelta(days=14 * i) for i in range(12)]  # 2-kurs har ikki haftada bir hafta
    for start in starts:
        DutyWeek.objects.create(start_date=start, created_by=admin)
        for i in range(7):
            day = generate_and_approve(start + dt.timedelta(days=i), admin)
            assert not day.warnings, (day.date, day.warnings)  # bo'sh o'rin yo'q
    assigned = Assignment.objects.filter(duty_day__status=DutyDay.Status.APPROVED)
    assert assigned.count() == 84 * 20
    assert not assigned.filter(cadet_id__in=exempt_ids).exists()

    # har 2-kurs haftasida har guruh ichida farq ≤ 1 (naryadga chiqadiganlar orasida)
    on_duty = {code: set(Cadet.objects.filter(group__code=code, gender=Gender.MALE, duty_exempt=False).values_list("pk", flat=True))
               for code in EXPECTED_ON_DUTY}
    for start in starts:
        week = Counter(assigned.filter(duty_day__week__start_date=start, post_slot__post__gender=Gender.MALE).values_list("cadet_id", flat=True))
        for code, ids in on_duty.items():
            counts = [week.get(i, 0) for i in ids]
            assert max(counts) - min(counts) <= 1, (start, code, sorted(counts))

    fair = {f.pool: f for f in stats.fairness_all(stats.Period())}
    assert fair["YuP-125"].members == 11 and fair["BI-525"].members == 16


def test_smallest_group_week_has_no_empty_slots(admin):
    """YuP-125 — 11 kishi: 7 sutkada bo'sh o'rin chiqmaydi, haftalik farq ≤ 1."""
    DutyWeek.objects.create(start_date=SUNDAY, created_by=admin)
    for i in range(7):
        generate_and_approve(SUNDAY + dt.timedelta(days=i), admin)
    assert not any(d.warnings for d in DutyDay.objects.all())
    assert Assignment.objects.count() == 7 * 20
    ids = list(Cadet.objects.filter(group__code="YuP-125", gender=Gender.MALE, duty_exempt=False).values_list("pk", flat=True))
    assert len(ids) == 11
    counts = Counter(Assignment.objects.filter(cadet_id__in=ids).values_list("cadet_id", flat=True))
    values = [counts.get(i, 0) for i in ids]
    # 7 sutkada guruh 6 joyning har birini kamida bir marta beradi (17 o'rin) va bittasini ikkinchi marta
    assert max(values) - min(values) <= 1 and 17 < sum(values) <= 21


# ---------------------------------------------------------------------------
# Qo'lda qo'yish va tasdiqlash
# ---------------------------------------------------------------------------


def test_manual_placement_of_exempt_is_rejected(admin):
    DutyWeek.objects.create(start_date=SUNDAY, created_by=admin)
    draft = services.generate_draft(SUNDAY, admin)
    group = StudyGroup.objects.get(code=INITIAL_ROTATION["noj1"])
    exempt = Cadet.objects.get(group=group, duty_exempt=True)
    slot = PostSlot.objects.get(post__code="noj1", position=1)
    candidates = days.replacement_candidates(draft, slot)
    excluded = {c.cadet.pk: c.excluded for c in candidates if c.excluded}
    assert "naryaddan ozod" in excluded[exempt.pk] and exempt.duty_position in excluded[exempt.pk]
    assert all(not c.cadet.duty_exempt for c in candidates if not c.excluded)
    with pytest.raises(ServiceError, match="naryaddan ozod"):
        days.replace_cadet(SUNDAY, slot.pk, exempt.pk, "sababli", "", admin, draft.version)


def test_exempt_in_draft_blocks_approval(admin, client):
    DutyWeek.objects.create(start_date=SUNDAY, created_by=admin)
    draft = services.generate_draft(SUNDAY, admin)
    a = draft.assignments.select_related("cadet").filter(post_slot__post__code="noj1").first()
    cadet_service.set_exempt(a.cadet, "BI-525 guruh komandiri o‘rinbosari", "buyruq", admin)
    issues = days.day_issues(draft)
    assert any(i.kind == "exempt" and i.blocks_approval for i in issues)
    with pytest.raises(ServiceError, match="Tasdiqlab bo‘lmaydi"):
        days.approve(SUNDAY, admin, draft.version)
    client.force_login(admin)
    html = client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()
    assert "naryaddan ozod" in html


def test_unexempted_cadet_goes_first(admin):
    """Ozoddan qaytgan kursantning jami hisobi kam — algoritm uni avtomatik oldinga qo'yadi (docs/02-algoritm.md)."""
    open_weeks(SUNDAY, 2, admin)
    for i in range(7):
        generate_and_approve(SUNDAY + dt.timedelta(days=i), admin)
    back = Cadet.objects.get(last_name="Tojiyev", first_name="Sherali")
    cadet_service.clear_exempt(back, "lavozimdan bo‘shadi", admin)
    nxt = SUNDAY + dt.timedelta(days=7)
    for i in range(7):
        day = generate_and_approve(nxt + dt.timedelta(days=i), admin)
        if day.assignments.filter(cadet=back).exists():
            break
    else:
        pytest.fail("Qaytgan kursant keyingi haftada naryadga tushmadi")
    # YuP-125 o'sha kuni bergan joyda u birinchi tanlanadi (jami 0)
    gpa = day.group_posts.get(group=back.group)
    first = day.assignments.filter(post_slot__post=gpa.post).order_by("post_slot__position").values_list("cadet_id", flat=True)
    assert back.pk in first


# ---------------------------------------------------------------------------
# Statistika
# ---------------------------------------------------------------------------


def test_stats_ignore_exempt(admin):
    DutyWeek.objects.create(start_date=SUNDAY, created_by=admin)
    for i in range(3):
        generate_and_approve(SUNDAY + dt.timedelta(days=i), admin)
    before = {f.pool: (f.members, f.min, f.max, f.mean, f.within_one_pct) for f in stats.fairness_all(stats.Period())}
    # ozodning o'tmishdagi naryadlari (lavozimga tayinlanishidan oldin) tarixda qoladi, lekin adolatga kirmaydi
    cadet = Cadet.objects.filter(group__code="BI-525", duty_exempt=False, gender=Gender.MALE).first()
    cadet_service.set_exempt(cadet, "Kurs navbatchisi yordamchisi", "buyruq", admin)
    after = {f.pool: f for f in stats.fairness_all(stats.Period())}
    assert after["BI-525"].members == 15
    assert before["BI-525"][0] == 16
    rows = {r.cadet.pk: r for r in stats.cadet_rows("BI-525", stats.Period())}
    assert cadet.pk in rows  # tarixda (jadvalda) ko'rinadi
    sections = {s.group.code: s for s in stats.group_sections(stats.Period())}
    assert sections["BI-525"].boys == 15 and sections["YuP-125"].boys == 11
    assert sections["YuP-125"].per_boy == round(sections["YuP-125"].total / 11, 2)
    comparison = stats.cadet_comparison(cadet)
    assert comparison["exempt"] and comparison["members"] == 15


def test_exempt_history_stays_on_card(admin, client):
    DutyWeek.objects.create(start_date=SUNDAY, created_by=admin)
    day = generate_and_approve(SUNDAY, admin)
    cadet = day.assignments.select_related("cadet").first().cadet
    cadet_service.set_exempt(cadet, "Kurs starshinasi o‘rinbosari", "buyruq", admin)
    client.force_login(admin)
    html = client.get(reverse("cadet_detail", args=[cadet.pk])).content.decode()
    assert 'data-testid="exempt-badge"' in html and "Kurs starshinasi o‘rinbosari" in html
    assert "13.09.2026" in html  # o'tmishdagi naryadi ko'rinadi


# ---------------------------------------------------------------------------
# Kursantlar sahifasi
# ---------------------------------------------------------------------------


def test_cadet_list_badge_filter_and_summary(admin, client):
    client.force_login(admin)
    html = client.get(reverse("cadet_list")).content.decode()
    for code, n in EXPECTED_ON_DUTY.items():
        assert f'data-testid="on-duty-{code}">{n}' in html
    assert "78" in html and "(9 ozod)" in html
    filtered = client.get(reverse("cadet_list"), {"holat": "ozod"})
    assert filtered.context["count"] == 9
    assert client.get(reverse("cadet_list"), {"holat": "naryadga", "jins": "M"}).context["count"] == 78


def test_admin_toggles_exempt_with_reason_and_log(admin, client):
    client.force_login(admin)
    c = Cadet.objects.filter(group__code="BI-425", duty_exempt=False, gender=Gender.MALE).first()
    url = reverse("cadet_exempt", args=[c.pk])
    client.post(url, {"position": "BI-425 guruh komandiri o‘rinbosari", "reason": ""})
    c.refresh_from_db()
    assert not c.duty_exempt  # sabab majburiy
    client.post(url, {"position": "BI-425 guruh komandiri o‘rinbosari", "reason": "Buyruq №12"})
    c.refresh_from_db()
    assert c.duty_exempt and c.is_active and c.duty_position == "BI-425 guruh komandiri o‘rinbosari"
    log = ChangeLog.objects.filter(cadet=c, action=ChangeLog.Action.CADET_EXEMPT).get()
    assert log.user == admin and log.reason == "Buyruq №12"

    client.post(reverse("cadet_unexempt", args=[c.pk]), {"reason": "Lavozimdan bo‘shadi"})
    c.refresh_from_db()
    assert not c.duty_exempt and c.duty_position == ""
    assert ChangeLog.objects.filter(cadet=c, action=ChangeLog.Action.CADET_UNEXEMPT, reason="Lavozimdan bo‘shadi").exists()
    assert c.pk in {e.id for e in services.engine_cadets()}  # yana nomzodlar hovuzida


def test_exempt_cadet_account_still_works(admin, client):
    c = Cadet.objects.filter(duty_exempt=True).first()
    user = User.objects.create_user("komandir", password=PASSWORD, role="cadet", cadet=c)
    assert client.login(username="komandir", password=PASSWORD)
    assert client.get(reverse("cadet_detail", args=[c.pk])).status_code == 200
    assert user.is_active and c.is_active
