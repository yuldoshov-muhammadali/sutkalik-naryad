"""Admin panel sahifalari ochilishini tekshirish (smoke test)."""

from __future__ import annotations

import datetime as dt

import pytest
from django.contrib import admin
from django.urls import reverse

from naryad import services
from naryad.models import Cadet, DutyWeek, User

from .conftest import INITIAL_ROTATION

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client_uz(client):
    user = User.objects.create_superuser("admin", password="x-12345678")
    client.force_login(user)
    return client


def test_all_changelists_and_add_pages_open(admin_client_uz, db_cadets):
    for model, model_admin in admin.site._registry.items():
        opts = model._meta
        resp = admin_client_uz.get(reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist"))
        assert resp.status_code == 200, opts.model_name
        add_url = reverse(f"admin:{opts.app_label}_{opts.model_name}_add")
        expected = 200 if model_admin.has_add_permission(_request(admin_client_uz)) else 403
        assert admin_client_uz.get(add_url).status_code == expected, opts.model_name


def test_duty_day_change_page_with_inlines(admin_client_uz, db_cadets):
    DutyWeek.objects.create(start_date=dt.date(2026, 9, 13))
    day = services.generate_draft(dt.date(2026, 9, 13), initial_rotation=INITIAL_ROTATION)
    resp = admin_client_uz.get(reverse("admin:naryad_dutyday_change", args=[day.pk]))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "tayinlash" in body.lower() and "jurnal" in body.lower()


def test_cadet_cannot_be_deleted_from_admin(admin_client_uz, db_cadets):
    cadet = Cadet.objects.first()
    resp = admin_client_uz.get(reverse("admin:naryad_cadet_delete", args=[cadet.pk]))
    assert resp.status_code == 403


def test_week_admin_rejects_monday(admin_client_uz):
    resp = admin_client_uz.post(reverse("admin:naryad_dutyweek_add"), {"start_date": "2026-09-14", "note": ""})
    assert resp.status_code == 200  # forma xato bilan qaytadi
    assert "yakshanba" in resp.content.decode()
    assert not DutyWeek.objects.exists()


def _request(client):
    from django.test import RequestFactory

    req = RequestFactory().get("/")
    req.user = User.objects.get(username="admin")
    return req


def test_cadet_cannot_enter_admin(client, db_cadets):
    """Kursant admin panelga kira olmaydi — na sessiya bilan, na parol bilan."""
    cadet = User.objects.create_user("kursant", password="x-12345678", role="cadet", cadet=db_cadets[0], is_staff=True)
    cadet.refresh_from_db()
    assert cadet.is_staff is False  # rol bo'yicha avtomatik
    client.force_login(cadet)
    for url in (reverse("admin:index"), reverse("admin:naryad_dutyweek_add")):
        resp = client.get(url)
        assert resp.status_code == 302 and "/admin/login/" in resp["Location"]
    client.logout()
    resp = client.post(reverse("admin:login"), {"username": "kursant", "password": "x-12345678"})
    assert resp.status_code == 200 and not resp.wsgi_request.user.is_authenticated


def test_removed_compiler_role_is_rejected_by_database(db):
    from django.db import IntegrityError, transaction

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user("eski", password="x-12345678", role="compiler")


def test_admin_role_without_superuser_has_full_access(client):
    boss = User.objects.create_user("kursboshligi", password="x-12345678", role="admin")
    assert boss.is_staff
    client.force_login(boss)
    assert client.get(reverse("admin:index")).status_code == 200
    assert client.get(reverse("admin:naryad_dutyweek_add")).status_code == 200
    assert client.get(reverse("admin:naryad_cadet_changelist")).status_code == 200


def test_settings_page_saves_initial_rotation(admin_client_uz, db_groups):
    from naryad.models import InitialRotation, Post, Setting

    url = reverse("admin:naryad_setting_change", args=[Setting.load().pk])
    assert admin_client_uz.get(url).status_code == 200
    s = Setting.load()
    data = {
        "recipient_position": s.recipient_position,
        "recipient_name": s.recipient_name,
        "course_head_position": s.course_head_position,
        "course_head_rank": s.course_head_rank,
        "course_head_name": s.course_head_name,
        "course_number": 2,
        "initial_rotation-TOTAL_FORMS": "6",
        "initial_rotation-INITIAL_FORMS": "0",
        "initial_rotation-MIN_NUM_FORMS": "0",
        "initial_rotation-MAX_NUM_FORMS": "6",
    }
    for i, (code, group) in enumerate(INITIAL_ROTATION.items()):
        data[f"initial_rotation-{i}-post"] = Post.objects.get(code=code).pk
        data[f"initial_rotation-{i}-group"] = db_groups[group].pk
    # avval 5 ta — xato
    partial = {k: v for k, v in data.items() if not k.startswith("initial_rotation-5-")}
    resp = admin_client_uz.post(url, partial)
    assert resp.status_code == 200 and "6 ta joyning har biri" in resp.content.decode()
    assert InitialRotation.objects.count() == 0
    resp = admin_client_uz.post(url, data)
    assert resp.status_code == 302
    assert InitialRotation.as_mapping() == INITIAL_ROTATION
