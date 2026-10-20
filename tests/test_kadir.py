"""22-bosqich: “Kadir” roli — admin bilan bir xil barcha amallar, faqat boshqaruv paneli (/admin/) va sozlamalarsiz."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from naryad import days
from naryad import permissions as perms
from naryad.models import Cadet, ChangeLog, DutyDay, Penalty, User

from .test_security import MONDAY, PASSWORD, POST_ONLY, SUNDAY, urls, world  # noqa: F401

pytestmark = pytest.mark.django_db

# Admin ko'radigan, kadir ko'rmaydigan sahifalar: Sozlamalar va sinov ma'lumotlarini tozalash (boshqaruv paneli bilan birga)
KADIR_FORBIDDEN = {"clear_test_data", "clear_test_data_run", "backup_download"}


@pytest.fixture
def kadir(world):  # noqa: F811
    return User.objects.create_user("kadir", password=PASSWORD, role="kadir", first_name="Kadir", last_name="Xodim")


def test_kadir_needs_no_cadet_and_is_not_staff(kadir):
    kadir.full_clean(exclude=["password"])
    assert kadir.cadet_id is None and not kadir.is_staff and not kadir.is_superuser
    assert perms.user_role(kadir) == perms.KADIR and not kadir.has_perm("naryad.change_setting")


def test_permission_table_kadir_has_everything_except_panel_and_settings():
    for action, (_, roles) in perms.PERMISSIONS.items():
        if action in ("settings.manage", "admin_panel", "cadets.status"):
            assert perms.KADIR not in roles, action
        elif perms.ADMIN in roles:
            assert perms.KADIR in roles, action
        else:  # kursant / komandir amallari (o'z kartochkasi, Mening guruhim, zalyot kiritish)
            assert perms.KADIR not in roles, action


def test_kadir_opens_every_admin_page_except_settings_and_clearing(client, world, kadir):  # noqa: F811
    client.force_login(kadir)
    for key, url in urls(world).items():
        if key in POST_ONLY:
            continue
        status = client.get(url).status_code
        if key in KADIR_FORBIDDEN:
            assert status in (403, 404), (key, status)
        elif key == "my_card" or key.startswith("group_"):  # kursant va komandir sahifalari
            assert status == 403, (key, status)
        elif key.startswith("admin_"):
            assert status == 302, (key, status)
        else:
            assert status in (200, 302), (key, url, status)


def test_kadir_cannot_enter_admin_panel_and_does_not_see_it(client, world, kadir):  # noqa: F811
    client.force_login(kadir)
    for url in ("/admin/", "/admin/naryad/cadet/", "/admin/naryad/setting/1/change/", "/admin/naryad/user/"):
        response = client.get(url)
        assert response.status_code == 302 and "/admin/login/" in response["Location"], url
    html = client.get(reverse("home")).content.decode()
    assert "Boshqaruv paneli" not in html and 'href="/admin/' not in html
    for name in ("week_list", "cadet_list", "stats", "penalty_list", "sick_list", "absence_list"):
        page = client.get(reverse(name)).content.decode()
        assert 'href="/admin/' not in page, name
    assert client.get(reverse("clear_test_data")).status_code == 403
    assert client.post(reverse("clear_test_data_run"), {"word_1": "TOZALASH", "word_2": "HAMMASI NOL", "token": "x"}).status_code == 403
    admin_html = client.get(reverse("home")).content.decode()
    assert "Kadir" in admin_html  # rol nomi pastki qatorda


def test_kadir_menu_matches_admin_menu_without_panel(client, world, kadir):  # noqa: F811
    client.force_login(world["admin"])
    admin_menu = [m["label"] for m in client.get(reverse("home")).context["menu"]]
    client.force_login(kadir)
    kadir_menu = [m["label"] for m in client.get(reverse("home")).context["menu"]]
    assert "Boshqaruv paneli" in admin_menu and "Boshqaruv paneli" not in kadir_menu
    assert kadir_menu == [m for m in admin_menu if m != "Boshqaruv paneli"]


def test_kadir_can_run_the_whole_duty_workflow(client, world, kadir):  # noqa: F811
    """Qoralamani tuzatadi, tasdiqlaydi, qayta ochadi, zalyot kiritadi, kursant qo'shadi — hammasi jurnalga o'z nomi bilan."""
    client.force_login(kadir)
    draft = world["draft"]
    slot = world["slot"]
    # almashtirish
    candidate = next(c for c in days.replacement_candidates(draft, slot) if not c.excluded and c.cadet.pk != draft.assignments.get(post_slot=slot).cadet_id)
    url = reverse("day_replace", args=[MONDAY.isoformat(), slot.pk])
    resp = client.post(url, {"cadet": candidate.cadet.pk, "reason": "sababli", "note": "", "version": draft.version})
    assert resp.status_code == 302
    assert ChangeLog.objects.filter(action="replace", user=kadir).exists()
    # tasdiqlash va qayta ochish
    draft.refresh_from_db()
    resp = client.post(reverse("day_approve", args=[MONDAY.isoformat()]), {"version": draft.version})
    assert resp.status_code == 302
    draft.refresh_from_db()
    assert DutyDay.objects.get(date=MONDAY).status == "approved" and DutyDay.objects.get(date=MONDAY).approved_by == kadir
    resp = client.post(reverse("day_reopen", args=[MONDAY.isoformat()]), {"version": DutyDay.objects.get(date=MONDAY).version, "reason": "Xato topildi"})
    assert resp.status_code == 302
    assert DutyDay.objects.get(date=MONDAY).status == "draft"
    # zalyot — admin qoidalari bilan (1–10 ta, komandir cheklovlari yo'q)
    boy = Cadet.objects.filter(gender="M", is_active=True, duty_exempt=False).exclude(pk=world["other"].pk).first()
    resp = client.post(reverse("penalty_list"), {"cadet": boy.pk, "reason_type": "tartib", "note": "Kechikdi",
                                                "order_date": SUNDAY.isoformat(), "count": 6})
    assert resp.status_code == 302
    penalty = Penalty.objects.get(cadet=boy)
    assert penalty.count == 6 and penalty.created_by == kadir
    # kursant qo'shish
    group = boy.group
    resp = client.post(reverse("cadet_create"), {"group": group.pk, "list_number": "99", "last_name": "Sinovov", "first_name": "Kadirjon",
                                                 "patronymic": "", "gender": "M", "short_name": ""})
    assert resp.status_code in (200, 302)
    # statistika va Excel
    assert client.get(reverse("stats")).status_code == 200 and client.get(reverse("stats_excel")).status_code == 200


def test_kadir_in_three_languages(client, world, kadir):  # noqa: F811
    for lang, title in (("uz", "Kadir"), ("ru", "Кадир"), ("en", "Kadir")):
        User.objects.filter(pk=kadir.pk).update(language=lang)
        client.force_login(kadir)
        html = client.get(reverse("home")).content.decode()
        assert title in html and "Boshqaruv paneli" not in html and "Admin panel" not in html


def test_kadir_role_needs_no_cadet_but_cadet_role_still_does(world):  # noqa: F811
    """Kadir roli uchun kursant shart emas, lekin kursant roli uchun hamon shart (eski qoida o'zgarmadi)."""
    with pytest.raises(ValidationError):
        User(username="x", role="cadet").full_clean(exclude=["password"])
    User(username="y", role="kadir").full_clean(exclude=["password"])


def test_kadir_has_no_deactivate_or_position_buttons_on_cadet_card(client, world, kadir):  # noqa: F811
    """1.13.1: faolsizlantirish va lavozim belgilash — faqat admin."""
    cadet = Cadet.objects.filter(gender="M", duty_exempt=False, is_active=True).first()
    holder = Cadet.objects.filter(duty_exempt=True).first()
    inactive = Cadet.objects.filter(gender="F").first()
    Cadet.objects.filter(pk=inactive.pk).update(is_active=False, deactivation_reason="Sinov")
    client.force_login(kadir)
    for c in (cadet, holder, inactive):
        html = client.get(reverse("cadet_detail", args=[c.pk])).content.decode()
        for word in ("Faolsizlantirish", "Qayta faollashtirish", "Lavozim belgilash", "Lavozimni olib tashlash",
                     reverse("cadet_deactivate", args=[c.pk]), reverse("cadet_exempt", args=[c.pk])):
            assert word not in html, (c.short_name, word)
        assert reverse("cadet_edit", args=[c.pk]) in html  # tahrirlash qoladi
    posts = [("cadet_deactivate", cadet, {"reason": "boshqa", "note": "x"}), ("cadet_exempt", cadet, {"position": "Kurs pisari", "reason": "x"}),
             ("cadet_unexempt", holder, {"reason": "x"}), ("cadet_activate", inactive, {})]
    for name, c, data in posts:
        assert client.post(reverse(name, args=[c.pk]), data).status_code == 403, name
    cadet.refresh_from_db(); holder.refresh_from_db(); inactive.refresh_from_db()
    assert cadet.is_active and not cadet.duty_exempt and holder.duty_exempt and not inactive.is_active
    # admin uchun tugmalar joyida
    client.force_login(world["admin"])
    html = client.get(reverse("cadet_detail", args=[cadet.pk])).content.decode()
    assert "Faolsizlantirish" in html and "Lavozim belgilash" in html
