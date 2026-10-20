"""10-bosqich: eng ko'p ishlatiladigan sahifalarda SQL so'rovlar soni cheklangan (N+1 qaytib kelmasin).

So'rovlar soni kursantlar va sutkalar soniga bog'liq bo'lmasligi kerak: ikki xil hajmdagi tarixda bir xil chegara.
"""

from __future__ import annotations

import datetime as dt

import pytest
from django.urls import reverse

from naryad import days, services
from naryad.models import Cadet, DutyWeek, InitialRotation, Post, StudyGroup, User

from .conftest import INITIAL_ROTATION

PASSWORD = "Kuchli-parol-2026"
SUNDAY = dt.date(2026, 9, 13)
pytestmark = pytest.mark.django_db

LIMITS = {
    "home": 19,  # 14-bosqich: ertangi ro'yxat banneri (+3: sozlama, 2 sutka, haftalar); 21-bosqich: og'ir joylar (+1)
    "week_list": 10,
    "cadet_list": 10,
    "approved_days": 8,
    "absence_list": 10,
    "stats": 26,  # 21-bosqich: og'ir joylar ro'yxati (sozlama, +1)
    "stats_excel": 25,
}


@pytest.fixture
def admin(db_cadets):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    return User.objects.create_user("kursboshligi", password=PASSWORD, role="admin")


def approve_days(admin, count):
    DutyWeek.objects.get_or_create(start_date=SUNDAY)
    for i in range(count):
        day = services.generate_draft(SUNDAY + dt.timedelta(days=i), admin)
        days.approve(day.date, admin, day.version)


@pytest.mark.parametrize("n_days", [1, 7])
def test_query_counts_do_not_grow_with_history(client, admin, django_assert_max_num_queries, n_days):
    approve_days(admin, n_days)
    client.force_login(admin)
    for name, limit in LIMITS.items():
        with django_assert_max_num_queries(limit):
            assert client.get(reverse(name)).status_code == 200, name
    for date in [SUNDAY, SUNDAY + dt.timedelta(days=n_days - 1)]:
        with django_assert_max_num_queries(20):
            client.get(reverse("day_detail", args=[date.isoformat()]))
    cadet = Cadet.objects.first()
    with django_assert_max_num_queries(13):  # 21-bosqich: joylar navbati kartochkasi (og'ir joylar sozlamasi, +1)
        client.get(reverse("cadet_detail", args=[cadet.pk]))
