"""23-bosqich: povtor (takroriy naryad) — CLAUDE.md 72-band.

Misol (INITIAL_ROTATION): yakshanba 1-Yotoqxonada BI-225, 2-NO‘J da BI-425, O‘quv binosida BI-325.
BI-225 e'tiroz oladi → dushanba 1-Yotoqxonada povtor (o'sha 3 kishi, o'sha lavozimlar), shu joyga navbati kelgan
BI-425 esa BI-225 ning navbatdagi joyi — O‘quv binosiga o'tadi (uning 1-Yotoqxonadagi navbati o'tdi).
Seshanba (Y variant): BI-225 → O‘quv binosi, BI-425 → Patrul.
"""

from __future__ import annotations

import datetime as dt

import pytest
from django.urls import reverse

from naryad import days, repeats, services, stats
from naryad.engine.allocator import History
from naryad.models import (
    Absence,
    Assignment,
    ChangeLog,
    DutyDay,
    DutyWeek,
    GroupPostAssignment,
    InitialRotation,
    Post,
    PostRepeat,
    StudyGroup,
    User,
)

from .conftest import INITIAL_ROTATION

SUNDAY = dt.date(2026, 9, 13)
MONDAY = SUNDAY + dt.timedelta(days=1)
TUESDAY = SUNDAY + dt.timedelta(days=2)
PASSWORD = "Kuchli-parol-2026"
pytestmark = pytest.mark.django_db


@pytest.fixture
def admin(db_cadets):
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


@pytest.fixture
def sunday(db_cadets, admin):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    DutyWeek.objects.create(start_date=SUNDAY)
    day = services.generate_draft(SUNDAY, admin)
    return days.approve(SUNDAY, admin, day.version)


def post_id(code: str) -> int:
    return Post.objects.get(code=code).pk


def mapping(day: DutyDay) -> dict[str, str]:
    return {g.post.code: g.group.code for g in day.group_posts.select_related("post", "group")}


def rows(date: dt.date, code: str) -> list[tuple[int, int, str]]:
    """(lavozim tartibi, kursant, tur) — joy bo'yicha."""
    return list(
        Assignment.objects.filter(duty_day__date=date, post_slot__post__code=code)
        .order_by("post_slot__position")
        .values_list("post_slot__position", "cadet_id", "kind")
    )


def approve(date: dt.date, admin) -> DutyDay:
    day = DutyDay.objects.get(date=date)
    return days.approve(date, admin, day.version)


def test_repeat_same_team_same_post_and_rotation_continues_from_actual(sunday, admin):
    before = rows(SUNDAY, "yotoq1")
    repeats.mark(SUNDAY, post_id("yotoq1"), "Kurs boshlig‘idan e’tiroz", admin)
    monday = services.generate_draft(MONDAY, admin)

    # 1) xuddi o'sha tarkib, xuddi o'sha lavozimlarda, povtor turi bilan
    assert [(pos, cid) for pos, cid, _ in rows(MONDAY, "yotoq1")] == [(pos, cid) for pos, cid, _ in before]
    assert {kind for _, _, kind in rows(MONDAY, "yotoq1")} == {Assignment.Kind.REPEAT}
    # 2) navbati kelgan BI-425 1-Yotoqxonaga yozilmaydi, BI-225 ning navbatdagi joyiga (O‘quv binosi) o'tadi
    m = mapping(monday)
    assert m["yotoq1"] == "BI-225" and m["oquv"] == "BI-425"
    assert m == {"markaz": "YuP-125", "noj1": "BI-625", "noj2": "BI-525", "yotoq1": "BI-225", "oquv": "BI-425", "patrul": "BI-325"}
    gpa = GroupPostAssignment.objects.get(duty_day=monday, post__code="yotoq1")
    assert gpa.is_repeat and gpa.skipped_group.code == "BI-425"
    assert not Assignment.objects.filter(duty_day=monday, post_slot__post__code="yotoq1", group__code="BI-425").exists()
    assert {kind for _, _, kind in rows(MONDAY, "oquv")} == {Assignment.Kind.NORMAL}
    assert not days.day_issues(monday)  # povtordagilar kecha turgani to'siq emas

    # 3) Y variant: guruhlar aylanishi amalda kim qayerda turganidan davom etadi
    approve(MONDAY, admin)
    tuesday = services.generate_draft(TUESDAY, admin)
    m = mapping(tuesday)
    assert m["oquv"] == "BI-225" and m["patrul"] == "BI-425" and m["markaz"] == "BI-325"
    repeated = {cid for _, cid, _ in before}
    assert not repeated & set(tuesday.assignments.values_list("cadet_id", flat=True))  # povtordan keyin dam oladi


def test_repeat_is_not_counted_in_personal_history(sunday, admin):
    repeated = [cid for _, cid, _ in rows(SUNDAY, "yotoq1")]
    repeats.mark(SUNDAY, post_id("yotoq1"), "E’tiroz", admin)
    services.generate_draft(MONDAY, admin)
    approve(MONDAY, admin)

    history = History(services.approved_history(), before=TUESDAY)
    for cid in repeated:
        assert len(history.of(cid)) == 1  # faqat yakshanbadagi oddiy naryad
    by_cadet = {r.cadet.pk: r for r in stats.build_rows(list(stats.pool_cadets("BI-225")), stats.Period())}
    assert all(by_cadet[cid].total == 1 and by_cadet[cid].this_week == 1 for cid in repeated)
    # guruhlar kesimi: BI-225 1-Yotoqxonada bir marta (povtor kirmaydi), BI-425 1-Yotoqxonada turmagan
    sections = {s.group.code: s for s in stats.group_sections(stats.Period())}
    assert sections["BI-225"].by_post["yotoq1"] == 1
    assert sections["BI-425"].by_post["yotoq1"] == 0 and sections["BI-425"].by_post["oquv"] == 1
    # O‘quv binosida turgan BI-425 kursantlari — oddiy naryad, hisobga kiradi
    oquv = [cid for _, cid, _ in rows(MONDAY, "oquv")]
    assert all(len(history.of(cid)) == 1 for cid in oquv)


def test_girls_repeat(sunday, admin):
    before = rows(SUNDAY, "qizlar")
    repeats.mark(SUNDAY, post_id("qizlar"), "E’tiroz", admin)
    monday = services.generate_draft(MONDAY, admin)
    assert [(p, c) for p, c, _ in rows(MONDAY, "qizlar")] == [(p, c) for p, c, _ in before]
    assert {k for _, _, k in rows(MONDAY, "qizlar")} == {Assignment.Kind.REPEAT}
    # o'g'il bolalar zanjiri o'zgarmaydi
    assert mapping(monday)["yotoq1"] == "BI-425"
    assert not GroupPostAssignment.objects.filter(duty_day=monday, is_repeat=True).exists()


def test_existing_draft_is_regenerated_on_mark_and_cancel(sunday, admin):
    services.generate_draft(MONDAY, admin)
    assert mapping(DutyDay.objects.get(date=MONDAY))["yotoq1"] == "BI-425"
    assert repeats.mark(SUNDAY, post_id("yotoq1"), "E’tiroz", admin) is True
    assert mapping(DutyDay.objects.get(date=MONDAY))["yotoq1"] == "BI-225"
    rp = PostRepeat.objects.get()
    assert repeats.cancel(SUNDAY, rp.pk, "Xato belgilangan", admin) is True
    monday = DutyDay.objects.get(date=MONDAY)
    assert mapping(monday)["yotoq1"] == "BI-425"
    assert not monday.assignments.filter(kind=Assignment.Kind.REPEAT).exists()
    actions = list(ChangeLog.objects.filter(day_date=SUNDAY).values_list("action", flat=True))
    assert ChangeLog.Action.REPEAT_ADD in actions and ChangeLog.Action.REPEAT_CANCEL in actions


def test_mark_rules(sunday, admin):
    yotoq = post_id("yotoq1")
    with pytest.raises(services.ServiceError, match="sababi majburiy"):
        repeats.mark(SUNDAY, yotoq, "  ", admin)
    repeats.mark(SUNDAY, yotoq, "E’tiroz", admin)
    with pytest.raises(services.ServiceError, match="allaqachon"):
        repeats.mark(SUNDAY, yotoq, "E’tiroz", admin)
    services.generate_draft(MONDAY, admin)
    with pytest.raises(services.ServiceError, match="faqat tasdiqlangan"):
        repeats.mark(MONDAY, yotoq, "E’tiroz", admin)  # qoralama
    approve(MONDAY, admin)
    with pytest.raises(services.ServiceError, match="tasdiqlangan"):
        repeats.mark(SUNDAY, post_id("oquv"), "E’tiroz", admin)  # keyingi sutka tasdiqlangan
    with pytest.raises(services.ServiceError, match="tasdiqlangan"):
        repeats.cancel(SUNDAY, PostRepeat.objects.get().pk, "Xato", admin)


def test_next_day_outside_open_week_is_blocked(sunday, admin):
    for i in range(1, 7):
        services.generate_draft(SUNDAY + dt.timedelta(days=i), admin)
        approve(SUNDAY + dt.timedelta(days=i), admin)
    saturday = SUNDAY + dt.timedelta(days=6)
    with pytest.raises(services.ServiceError, match="2-kurs haftasiga tegishli emas"):
        repeats.mark(saturday, post_id("yotoq1"), "E’tiroz", admin)


def test_reopening_source_day_drops_repeat(sunday, admin):
    repeats.mark(SUNDAY, post_id("yotoq1"), "E’tiroz", admin)
    days.reopen(SUNDAY, "Tuzatish kerak", admin, DutyDay.objects.get(date=SUNDAY).version)
    assert not PostRepeat.objects.exists()
    assert ChangeLog.objects.filter(day_date=SUNDAY, action=ChangeLog.Action.REPEAT_CANCEL).exists()


def test_absent_repeat_cadet_leaves_slot_for_admin(sunday, admin):
    (_, first, _), *_ = rows(SUNDAY, "yotoq1")
    Absence.objects.create(cadet_id=first, start_date=MONDAY, end_date=MONDAY, reason_type="kasal", created_by=admin)
    repeats.mark(SUNDAY, post_id("yotoq1"), "E’tiroz", admin)
    monday = services.generate_draft(MONDAY, admin)
    assert len(rows(MONDAY, "yotoq1")) == 2  # o'rin bo'sh — generator boshqani qo'ymaydi
    assert any(i.kind == "empty" for i in days.day_issues(monday))
    with pytest.raises(services.ServiceError):
        days.approve(MONDAY, admin, monday.version)


def test_swap_keeps_repeat_kind(sunday, admin):
    repeats.mark(SUNDAY, post_id("yotoq1"), "E’tiroz", admin)
    monday = services.generate_draft(MONDAY, admin)
    a, b = [r for r in rows(MONDAY, "yotoq1")][:2]
    days.swap_slots(MONDAY, monday.assignments.get(cadet_id=a[1]).post_slot_id, monday.assignments.get(cadet_id=b[1]).post_slot_id,
                    "boshqa", "Lavozim almashdi", admin, monday.version)
    assert {k for _, _, k in rows(MONDAY, "yotoq1")} == {Assignment.Kind.REPEAT}


def test_pages_and_roles(client, sunday, admin):
    client.force_login(admin)
    page = client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()
    assert 'data-testid="repeat-form"' in page
    response = client.post(reverse("day_repeat", args=[SUNDAY.isoformat()]), {"post": post_id("yotoq1"), "reason": "E’tiroz"})
    assert response.status_code == 302 and PostRepeat.objects.count() == 1
    services.generate_draft(MONDAY, admin)
    page = client.get(reverse("day_detail", args=[MONDAY.isoformat()])).content.decode()
    assert 'data-testid="repeat-badge"' in page and 'data-testid="repeat-notices"' in page
    assert "BI-425 guruhining bu joydagi navbati o‘tdi." in page

    # kadir — admin bilan bir xil; kursant — 403
    kadir = User.objects.create_user("kadir", password=PASSWORD, role="kadir")
    client.force_login(kadir)
    rp = PostRepeat.objects.get()
    response = client.post(reverse("day_repeat_cancel", args=[SUNDAY.isoformat(), rp.pk]), {"reason": "Xato"})
    assert response.status_code == 302 and not PostRepeat.objects.exists()
    approve(MONDAY, admin)
    cadet_user = User.objects.create_user("kursant", password=PASSWORD, role="cadet",
                                          cadet_id=rows(SUNDAY, "yotoq1")[0][1])
    client.force_login(cadet_user)
    assert client.post(reverse("day_repeat", args=[SUNDAY.isoformat()]), {"post": post_id("yotoq1"), "reason": "x"}).status_code == 403
    page = client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()
    assert "repeat-form" not in page and "repeat-panel" not in page
