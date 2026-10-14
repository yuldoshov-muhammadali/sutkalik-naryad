"""services.py: tarixni engine'ga aylantirish va sutka qoralamasini saqlash."""

from __future__ import annotations

import datetime as dt

import pytest
from django.utils import timezone

from naryad import services
from naryad.engine.config import ROTATION_CHAIN
from naryad.models import Absence, Assignment, Cadet, ChangeLog, DutyDay, DutyWeek, GroupPostAssignment

from .conftest import INITIAL_ROTATION

SUNDAY = dt.date(2026, 9, 13)

pytestmark = pytest.mark.django_db


@pytest.fixture
def week(db):
    return DutyWeek.objects.create(start_date=SUNDAY)


def approve(day: DutyDay) -> DutyDay:
    day.status = DutyDay.Status.APPROVED
    day.approved_at = timezone.now()
    day.save()
    return day


def test_generate_and_save_one_day(week, db_cadets):
    day = services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION)

    assert day.status == DutyDay.Status.DRAFT
    assert day.week == week
    assert day.warnings == []
    assert day.assignments.count() == 20
    assert GroupPostAssignment.objects.filter(duty_day=day).count() == 6
    assert {g.post.code: g.group.code for g in day.group_posts.all()} == INITIAL_ROTATION
    assert set(day.assignments.values_list("source", flat=True)) == {Assignment.Source.AUTO}
    # har joy bitta guruhdan, qizlar faqat qizlar yotoqxonasida
    for a in day.assignments.select_related("post_slot__post", "cadet__group"):
        assert a.cadet.gender == a.post_slot.post.gender
        if a.post_slot.post.code != "qizlar":
            assert a.cadet.group.code == INITIAL_ROTATION[a.post_slot.post.code]
        assert a.group_id == a.cadet.group_id
    assert ChangeLog.objects.filter(duty_day=day, action=ChangeLog.Action.GENERATE).count() == 1


def test_draft_does_not_enter_history(week, db_cadets):
    services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION)
    assert services.approved_history() == []


def test_next_day_after_approval_rotates_groups(week, db_cadets):
    first = approve(services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION))
    history = services.approved_history()
    assert len(history) == 20 and all(r.day == SUNDAY for r in history)

    second = services.generate_draft(SUNDAY + dt.timedelta(days=1))
    prev = {g.post.code: g.group.code for g in first.group_posts.all()}
    cur = {g.post.code: g.group.code for g in second.group_posts.all()}
    for i, code in enumerate(ROTATION_CHAIN):
        assert cur[ROTATION_CHAIN[(i + 1) % 6]] == prev[code]
    yesterday = set(first.assignments.values_list("cadet_id", flat=True))
    assert not yesterday & set(second.assignments.values_list("cadet_id", flat=True))


def test_regenerating_draft_replaces_it(week, db_cadets):
    a = services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION)
    b = services.generate_draft(SUNDAY)  # admin kiritgan taqsimot qoralamadan olinadi
    assert a.pk == b.pk
    assert DutyDay.objects.count() == 1
    assert b.assignments.count() == 20
    assert ChangeLog.objects.filter(duty_day=b, action=ChangeLog.Action.GENERATE).count() == 2


def test_day_outside_opened_week_is_rejected(db_cadets):
    with pytest.raises(services.ServiceError, match="haftasiga tegishli emas"):
        services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION)


def test_first_day_requires_initial_rotation(week, db_cadets):
    with pytest.raises(services.ServiceError, match="Tarix bo‘sh"):
        services.generate_draft(SUNDAY)


def test_days_are_generated_one_by_one(week, db_cadets):
    services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION)
    with pytest.raises(services.ServiceError, match="qoralamasini tasdiqlang"):
        services.generate_draft(SUNDAY + dt.timedelta(days=1))


def test_cannot_skip_days_in_week(week, db_cadets):
    approve(services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION))
    with pytest.raises(services.ServiceError, match="tuzilmagan/tasdiqlanmagan"):
        services.generate_draft(SUNDAY + dt.timedelta(days=2))


def test_approved_day_cannot_be_regenerated(week, db_cadets):
    approve(services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION))
    with pytest.raises(services.ServiceError, match="allaqachon tasdiqlangan"):
        services.generate_draft(SUNDAY)


def test_absent_cadet_from_database_is_skipped(week, db_cadets):
    target = next(c for c in db_cadets if c.group.code == INITIAL_ROTATION["noj1"] and c.gender == "M")
    Absence.objects.create(cadet=target, start_date=SUNDAY, end_date=SUNDAY, reason_type="kasal")
    day = services.generate_draft(SUNDAY, initial_rotation=INITIAL_ROTATION)
    assert target.pk not in set(day.assignments.values_list("cadet_id", flat=True))


def test_engine_conversion_roundtrip(db_cadets):
    cadets = services.engine_cadets()
    assert len(cadets) == 91  # 100 − 9 naryaddan ozod (nomzodlar hovuziga kirmaydi)
    assert not {c.id for c in cadets} & set(Cadet.objects.filter(duty_exempt=True).values_list("pk", flat=True))
    first = cadets[0]
    assert (first.id, first.group, first.gender, first.short_name) == (1, "YuP-125", "F", "Abduvaliyeva R")
