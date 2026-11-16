"""24-bosqich: almashtirishda barcha guruhlar va lavozimdagilar; boshqa kurs kursantini qo'lda kiritish (CLAUDE.md 73-band)."""

from __future__ import annotations

import datetime as dt

import pytest
from django.urls import reverse

from naryad import days, pdf, services, stats
from naryad.engine.allocator import History
from naryad.models import (
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    InitialRotation,
    OutsiderAssignment,
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
def draft(db_cadets, admin):
    for code, group in INITIAL_ROTATION.items():
        InitialRotation.objects.create(post=Post.objects.get(code=code), group=StudyGroup.objects.get(code=group))
    DutyWeek.objects.create(start_date=SUNDAY)
    return services.generate_draft(SUNDAY, admin)


def slot(code: str, position: int = 1) -> PostSlot:
    return PostSlot.objects.get(post__code=code, position=position)


def version(date: dt.date = SUNDAY) -> int:
    return DutyDay.objects.get(date=date).version


def approve(date: dt.date, admin) -> DutyDay:
    return days.approve(date, admin, version(date))


def mapping(date: dt.date) -> dict[str, str]:
    return {g.post.code: g.group.code for g in DutyDay.objects.get(date=date).group_posts.select_related("post", "group")}


def outsider(code: str, position: int, admin, name="Karimov A", course=3, group="BI-324", reason="boshqa", note="Bildirgi"):
    return days.place_outsider(SUNDAY, slot(code, position).pk, name, course, group, reason, note, admin, version())


# ---------------------------------------------------------------------------
# 1. Almashtirish oynasi: barcha guruhlar va lavozimdagilar
# ---------------------------------------------------------------------------


def test_candidates_include_all_groups_and_exempt_in_order(draft):
    candidates = days.replacement_candidates(draft, slot("noj1"))
    groups = {c.cadet.group.code for c in candidates}
    assert groups == {g.code for g in StudyGroup.objects.all()}
    assert any(c.cadet.duty_exempt and not c.excluded for c in candidates)
    sections = [c.section for c in candidates]
    assert sections == sorted(sections, key=["own", "other", "exempt"].index)  # avval shu joy guruhi
    assert candidates[0].best and candidates[0].cadet.group.code == INITIAL_ROTATION["noj1"]
    assert all(c.cadet.gender == "M" for c in candidates)  # qizlar o'g'il joyiga emas


def test_other_group_cadet_counts_in_own_history_and_chain_holds(draft, admin):
    busy = set(draft.assignments.values_list("cadet_id", flat=True))
    other = Cadet.objects.filter(gender="M", duty_exempt=False, group__code="BI-625").exclude(pk__in=busy).first()
    days.replace_cadet(SUNDAY, slot("noj1").pk, other.pk, "boshqa", "Kurs boshlig‘i topshirig‘i", admin, version())
    a = Assignment.objects.get(duty_day__date=SUNDAY, post_slot=slot("noj1"))
    assert a.cadet == other and a.group.code == "BI-625" and a.kind == Assignment.Kind.NORMAL
    approve(SUNDAY, admin)
    assert len(History(services.approved_history(), before=MONDAY).of(other.pk)) == 1
    services.generate_draft(MONDAY, admin)  # zanjir buzilmaydi: 1-NO‘J guruhi (BI-525) 2-NO‘J ga o'tadi
    assert mapping(MONDAY)["noj2"] == INITIAL_ROTATION["noj1"]


def test_page_shows_section_headings(client, draft, admin):
    client.force_login(admin)
    html = client.get(reverse("day_replace", args=[SUNDAY.isoformat(), slot("noj1").pk]), HTTP_HX_REQUEST="true").content.decode()
    assert 'data-testid="section-other"' in html and 'data-testid="section-exempt"' in html


# ---------------------------------------------------------------------------
# 3–4. Boshqa kurs kursanti
# ---------------------------------------------------------------------------


def test_outsider_replaces_cadet_without_history(draft, admin):
    replaced = Assignment.objects.get(duty_day=draft, post_slot=slot("noj1", 3)).cadet
    outsider("noj1", 3, admin)
    assert not Assignment.objects.filter(duty_day=draft, post_slot=slot("noj1", 3)).exists()
    o = OutsiderAssignment.objects.get()
    assert (o.full_name, o.course, o.group_name) == ("Karimov A", 3, "BI-324")
    assert not days.day_issues(draft)  # o'rin band — bo'sh hisoblanmaydi
    approve(SUNDAY, admin)
    assert not Assignment.objects.filter(cadet=replaced).exists()  # platforma tanlagan kursantga hech narsa yozilmadi
    log = ChangeLog.objects.get(action=ChangeLog.Action.OUTSIDER_ADD)
    assert replaced.short_name in log.details and "Karimov A (3-kurs, BI-324)" in log.details and log.reason == "Bildirgi"
    rows = {r.cadet.pk for r in stats.build_rows(list(Cadet.objects.all()), stats.Period()) if r.total}
    assert replaced.pk not in rows


def test_whole_post_by_outsiders_passes_group_turn(draft, admin):
    group = INITIAL_ROTATION["noj1"]
    for position in range(1, 5):
        outsider("noj1", position, admin, name=f"Boshqa {position}")
    approve(SUNDAY, admin)
    assert not Assignment.objects.filter(duty_day__date=SUNDAY, post_slot__post__code="noj1").exists()
    services.generate_draft(MONDAY, admin)
    assert mapping(MONDAY)["noj2"] == group  # guruh navbati o'tdi — zanjir buzilmadi
    assert mapping(MONDAY)["noj1"] == INITIAL_ROTATION["markaz"]
    # guruh kesimida 1-NO‘J guruh hisobiga
    sections = {s.group.code: s for s in stats.group_sections(stats.Period())}
    assert sections[group].by_post["noj1"] == 1


def test_pdf_shows_outsider_in_same_form(draft, admin):
    outsider("noj1", 2, admin, name="Toshmatov B", course=1, group="BI-126")
    approve(SUNDAY, admin)
    html = pdf.render_html([DutyDay.objects.get(date=SUNDAY)])
    assert "Toshmatov B" in html and "BI-126" in html
    assert "1-kurs" not in html  # kurs PDF’ga yozilmaydi (6-savol: A)
    assert pdf.render_pdf([DutyDay.objects.get(date=SUNDAY)])[:4] == b"%PDF"


def test_outsider_replaced_back_by_cadet(draft, admin):
    outsider("noj1", 3, admin)
    cand = next(c.cadet for c in days.replacement_candidates(DutyDay.objects.get(date=SUNDAY), slot("noj1", 3)) if c.best)
    days.replace_cadet(SUNDAY, slot("noj1", 3).pk, cand.pk, "boshqa", "Qaytarildi", admin, version())
    assert not OutsiderAssignment.objects.exists()
    log = ChangeLog.objects.filter(action=ChangeLog.Action.REPLACE).latest("id")
    assert "Boshqa kurs kursanti Karimov A" in log.details


def test_outsider_validation_and_sick_reason(draft, admin):
    with pytest.raises(services.ServiceError, match="Ism-familiyani"):
        outsider("noj1", 3, admin, name="  ")
    with pytest.raises(services.ServiceError, match="Kursni"):
        outsider("noj1", 3, admin, course=2)
    with pytest.raises(services.ServiceError, match="Guruhni"):
        outsider("noj1", 3, admin, group="")
    with pytest.raises(services.ServiceError, match="izoh majburiy"):
        outsider("noj1", 3, admin, note="")
    replaced = Assignment.objects.get(duty_day=draft, post_slot=slot("noj1", 3)).cadet
    outsider("noj1", 3, admin, reason="kasal", note="")
    assert Absence.objects.filter(cadet=replaced, start_date=SUNDAY, reason_type="kasal").exists()


def test_regenerate_removes_outsiders_and_approved_day_is_locked(draft, admin):
    outsider("noj1", 3, admin)
    services.generate_draft(SUNDAY, admin)
    assert not OutsiderAssignment.objects.exists()
    outsider("noj1", 3, admin)
    approve(SUNDAY, admin)
    with pytest.raises(services.ServiceError, match="tasdiqlangan"):
        outsider("noj1", 4, admin)


def test_pages_for_admin_and_cadet(client, draft, admin):
    client.force_login(admin)
    url = reverse("day_outsider", args=[SUNDAY.isoformat(), slot("noj1", 3).pk])
    assert 'data-testid="outsider-form"' in client.get(url).content.decode()
    response = client.post(url, {"full_name": "Karimov A", "course": "3", "group_name": "BI-324", "reason": "boshqa",
                                 "note": "Bildirgi", "version": version()})
    assert response.status_code == 302 and OutsiderAssignment.objects.count() == 1
    html = client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()
    assert "Karimov A" in html and 'data-testid="outsider-badge"' in html and 'data-testid="outsider-button"' in html
    approve(SUNDAY, admin)
    cadet = User.objects.create_user("kursant", password=PASSWORD, role="cadet", cadet=Cadet.objects.first())
    client.force_login(cadet)
    html = client.get(reverse("day_detail", args=[SUNDAY.isoformat()])).content.decode()
    assert "Karimov A" in html and "BI-324" in html and "outsider-button" not in html
    assert client.post(url, {"full_name": "X", "course": "3", "group_name": "Y", "reason": "boshqa", "note": "x"}).status_code == 403
