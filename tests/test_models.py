"""Model cheklovlari testlari (pytest-django)."""

from __future__ import annotations

import datetime as dt

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from naryad.engine.config import POSTS as ENGINE_POSTS
from naryad.models import (
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    GroupPostAssignment,
    Post,
    PostSlot,
    Setting,
    User,
    UserRole,
)

SUNDAY = dt.date(2026, 9, 13)

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Joylar migratsiyasi
# ---------------------------------------------------------------------------


def test_posts_migration_matches_engine_config():
    assert Post.objects.count() == 7
    assert PostSlot.objects.count() == 20
    for ep in ENGINE_POSTS:
        post = Post.objects.get(code=ep.code)
        assert (post.name, post.gender, post.display_order, post.rotation_index) == (
            ep.name,
            ep.gender,
            ep.display_order,
            ep.rotation_index,
        )
        slots = list(post.slots.order_by("position").values_list("position", "role", "print_label", "show_label"))
        assert slots == [(s.position, s.role, s.pdf_label, s.show_label) for s in ep.slots]


def test_setting_is_singleton():
    s = Setting.load()
    assert s.pk == 1 and s.recipient_name == "X.Sattorovga" and s.course_title == "2-kurs ro‘yxati"
    Setting(course_number=3).save()
    assert Setting.objects.count() == 1
    assert Setting.load().course_number == 3


# ---------------------------------------------------------------------------
# Hafta va sutka
# ---------------------------------------------------------------------------


def test_week_must_start_on_sunday():
    week = DutyWeek(start_date=dt.date(2026, 9, 14))  # dushanba
    with pytest.raises(ValidationError) as exc:
        week.full_clean()
    assert "start_date" in exc.value.message_dict


def test_week_on_sunday_is_valid_and_spans_7_duty_days():
    week = DutyWeek(start_date=SUNDAY)
    week.full_clean()
    week.save()
    assert week.end_date == dt.date(2026, 9, 19)
    assert len(week.dates) == 7
    assert week.start_at.isoformat() == "2026-09-13T18:00:00+05:00"
    assert week.end_at.isoformat() == "2026-09-20T18:00:00+05:00"


def test_overlapping_weeks_rejected():
    DutyWeek.objects.create(start_date=SUNDAY)
    DutyWeek(start_date=SUNDAY + dt.timedelta(days=14)).full_clean()  # 2 haftadan keyin — mumkin
    with pytest.raises(ValidationError):
        DutyWeek(start_date=SUNDAY).full_clean()  # aynan o'sha hafta (unique)


def test_day_outside_week_rejected():
    week = DutyWeek.objects.create(start_date=SUNDAY)
    with pytest.raises(ValidationError) as exc:
        DutyDay(week=week, date=SUNDAY + dt.timedelta(days=7)).full_clean()  # keyingi yakshanba
    assert "date" in exc.value.message_dict
    with pytest.raises(ValidationError):
        DutyDay(week=week, date=SUNDAY - dt.timedelta(days=1)).full_clean()


def test_day_inside_week_is_valid_and_starts_at_18():
    week = DutyWeek.objects.create(start_date=SUNDAY)
    day = DutyDay(week=week, date=dt.date(2026, 9, 18))
    day.full_clean()
    day.save()
    assert day.start_at.isoformat() == "2026-09-18T18:00:00+05:00"
    assert day.end_at.isoformat() == "2026-09-19T18:00:00+05:00"


def test_approved_day_requires_approval_time():
    week = DutyWeek.objects.create(start_date=SUNDAY)
    with pytest.raises(IntegrityError), transaction.atomic():
        DutyDay.objects.create(week=week, date=SUNDAY, status=DutyDay.Status.APPROVED)


# ---------------------------------------------------------------------------
# Unique cheklovlar
# ---------------------------------------------------------------------------


@pytest.fixture
def day(db):
    week = DutyWeek.objects.create(start_date=SUNDAY)
    return DutyDay.objects.create(week=week, date=SUNDAY)


def _male(cadets, group, n=0):
    return [c for c in cadets if c.group.code == group and c.gender == "M"][n]


def test_cadet_cannot_take_two_slots_same_day(day, db_cadets):
    cadet = _male(db_cadets, "BI-525")
    noj1 = list(PostSlot.objects.filter(post__code="noj1").order_by("position"))
    Assignment.objects.create(duty_day=day, post_slot=noj1[0], cadet=cadet)
    with pytest.raises(IntegrityError), transaction.atomic():
        Assignment.objects.create(duty_day=day, post_slot=noj1[1], cadet=cadet)


def test_slot_cannot_have_two_cadets_same_day(day, db_cadets):
    slot = PostSlot.objects.get(post__code="markaz", position=1)
    Assignment.objects.create(duty_day=day, post_slot=slot, cadet=_male(db_cadets, "BI-625", 0))
    with pytest.raises(IntegrityError), transaction.atomic():
        Assignment.objects.create(duty_day=day, post_slot=slot, cadet=_male(db_cadets, "BI-625", 1))


def test_group_post_assignment_unique_per_day(day, db_groups):
    noj1 = Post.objects.get(code="noj1")
    noj2 = Post.objects.get(code="noj2")
    GroupPostAssignment.objects.create(duty_day=day, post=noj1, group=db_groups["BI-525"])
    with pytest.raises(IntegrityError), transaction.atomic():
        GroupPostAssignment.objects.create(duty_day=day, post=noj1, group=db_groups["BI-425"])  # joy band
    with pytest.raises(IntegrityError), transaction.atomic():
        GroupPostAssignment.objects.create(duty_day=day, post=noj2, group=db_groups["BI-525"])  # guruh band


def test_assignment_gender_and_group_validation(day, db_cadets, db_groups):
    girl = next(c for c in db_cadets if c.gender == "F")
    slot = PostSlot.objects.get(post__code="noj1", position=1)
    with pytest.raises(ValidationError):
        Assignment(duty_day=day, post_slot=slot, cadet=girl, group=girl.group).full_clean()
    GroupPostAssignment.objects.create(duty_day=day, post=slot.post, group=db_groups["BI-525"])
    other = _male(db_cadets, "BI-425")
    with pytest.raises(ValidationError):
        Assignment(duty_day=day, post_slot=slot, cadet=other, group=other.group).full_clean()


# ---------------------------------------------------------------------------
# Kursant, yo'qlik, jurnal, foydalanuvchi
# ---------------------------------------------------------------------------


def test_cadet_short_name_and_apostrophes(db_groups):
    c = Cadet.objects.create(group=db_groups["BI-625"], last_name="G'ayratov", first_name="G‘iyosiddin", gender="M")
    assert c.last_name == "G‘ayratov"
    assert c.short_name == "G‘ayratov G‘"


def test_cadet_deactivation_requires_reason(db_cadets):
    cadet = db_cadets[0]
    cadet.is_active = False
    with pytest.raises(ValidationError):
        cadet.full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        cadet.save()
    cadet.deactivation_reason = "Boshqa kursga o‘tdi"
    cadet.save()
    cadet.refresh_from_db()
    assert cadet.deactivated_at is not None


def test_cadet_with_history_cannot_be_deleted(day, db_cadets):
    cadet = _male(db_cadets, "BI-625")
    Assignment.objects.create(duty_day=day, post_slot=PostSlot.objects.get(post__code="markaz"), cadet=cadet)
    from django.db.models import ProtectedError

    with pytest.raises(ProtectedError):
        cadet.delete()


def test_absence_dates_checked(db_cadets):
    with pytest.raises(IntegrityError), transaction.atomic():
        Absence.objects.create(cadet=db_cadets[0], start_date=SUNDAY, end_date=SUNDAY - dt.timedelta(days=1), reason_type="kasal")
    with pytest.raises(ValidationError):
        Absence(cadet=db_cadets[0], start_date=SUNDAY, end_date=SUNDAY, reason_type="boshqa").full_clean()


def test_changelog_reason_required_for_replace(day):
    with pytest.raises(IntegrityError), transaction.atomic():
        ChangeLog.objects.create(duty_day=day, action=ChangeLog.Action.REPLACE, reason="")
    ChangeLog.objects.create(duty_day=day, action=ChangeLog.Action.GENERATE)


def test_superuser_gets_admin_role():
    user = User.objects.create_superuser("kursboshligi", password="x-12345678")
    assert user.role == UserRole.ADMIN
    assert user.is_admin_role
