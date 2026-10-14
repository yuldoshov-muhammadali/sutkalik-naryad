"""Taqsimlash algoritmi testlari (CLAUDE.md 4- va 10-bo'limlar)."""

from __future__ import annotations

import datetime as dt
from collections import Counter

import pytest

from naryad.engine import AllocationError, assign_roles, generate_day, rotate_groups, week_bounds, week_start
from naryad.engine.allocator import History
from naryad.engine.config import MALE_POSTS, POSTS_BY_CODE, ROTATION_CHAIN
from naryad.engine.models import FEMALE, MALE, ROLE_DUTY, ROLE_GUARD, Absence, Cadet, Record
from naryad.engine.names import first_letter, normalize_apostrophes, short_name

from .conftest import INITIAL_ROTATION, WEEK_START, simulate

# ---------------------------------------------------------------------------
# Vaqt
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "day, expected",
    [
        (dt.date(2026, 9, 13), dt.date(2026, 9, 13)),  # yakshanba — yangi hafta boshlanadi
        (dt.date(2026, 9, 18), dt.date(2026, 9, 13)),  # juma
        (dt.date(2026, 9, 19), dt.date(2026, 9, 13)),  # shanba — haftaning 7-sutkasi
        (dt.date(2026, 9, 20), dt.date(2026, 9, 20)),  # keyingi yakshanba — yangi hafta
    ],
)
def test_week_start(day, expected):
    assert week_start(day) == expected


def test_week_bounds_is_sunday_18_to_sunday_18():
    start, end = week_bounds(dt.date(2026, 9, 18))
    assert start == dt.datetime(2026, 9, 13, 18, 0)
    assert end == dt.datetime(2026, 9, 20, 18, 0)
    assert start.weekday() == 6 and end.weekday() == 6


# ---------------------------------------------------------------------------
# 1-daraja: guruhlar aylanishi
# ---------------------------------------------------------------------------


def test_rotation_requires_initial_mapping_without_history():
    with pytest.raises(AllocationError):
        rotate_groups(sorted(INITIAL_ROTATION.values()), [], day=WEEK_START)


def test_rotation_moves_each_group_to_next_post(week):
    results, _ = week
    for prev, cur in zip(results, results[1:]):
        for i, code in enumerate(ROTATION_CHAIN):
            nxt = ROTATION_CHAIN[(i + 1) % len(ROTATION_CHAIN)]
            assert cur.group_by_post[nxt] == prev.group_by_post[code]


def test_group_never_same_post_two_days_in_row(week):
    results, _ = week
    for prev, cur in zip(results, results[1:]):
        for code in ROTATION_CHAIN:
            assert prev.group_by_post[code] != cur.group_by_post[code]


def test_six_days_each_group_visits_each_post_once(week):
    results, _ = week
    for group in INITIAL_ROTATION.values():
        posts = [next(p for p, g in r.group_by_post.items() if g == group) for r in results[:6]]
        assert sorted(posts) == sorted(ROTATION_CHAIN)


def test_rotation_continues_into_next_week(cadets, week):
    results, history = week
    nxt = generate_day(WEEK_START + dt.timedelta(days=14), cadets, history)
    last = results[-1]
    for i, code in enumerate(ROTATION_CHAIN):
        assert nxt.group_by_post[ROTATION_CHAIN[(i + 1) % 6]] == last.group_by_post[code]


# ---------------------------------------------------------------------------
# Sutka tarkibi
# ---------------------------------------------------------------------------


def test_every_day_has_exactly_20_people(week):
    results, _ = week
    for r in results:
        assert len(r.assignments) == 20
        assert len(r.filled) == 20
        assert not r.warnings
        ids = [a.cadet_id for a in r.filled]
        assert len(ids) == len(set(ids)), "bir kursant bir sutkada faqat bitta o'rinda"


def test_each_post_is_filled_by_one_group(week, cadets):
    by_id = {c.id: c for c in cadets}
    results, _ = week
    for r in results:
        for post in MALE_POSTS:
            groups = {by_id[a.cadet_id].group for a in r.filled if a.slot.post == post.code}
            assert groups == {r.group_by_post[post.code]}
            assert all(by_id[a.cadet_id].gender == MALE for a in r.filled if a.slot.post == post.code)


def test_girls_only_in_girls_dormitory(week, cadets):
    by_id = {c.id: c for c in cadets}
    results, _ = week
    for r in results:
        for a in r.filled:
            assert (by_id[a.cadet_id].gender == FEMALE) == (a.slot.post == "qizlar")


# ---------------------------------------------------------------------------
# 2-daraja: adolat
# ---------------------------------------------------------------------------


def _pools(cadets):
    pools = {}
    for c in cadets:
        key = c.group if c.gender == MALE else "qizlar"
        pools.setdefault(key, []).append(c.id)
    return pools


def test_nobody_twice_before_everyone_once(week, cadets):
    """Bir hafta ichida hovuzdagi hamma bir marta turmaguncha hech kim ikkinchi marta tushmaydi.

    Agar biror sutkada ikkinchi marta turayotgan kursant tanlansa, shu paytgacha
    turmagan barcha munosib hovuzdoshlari ham aynan shu sutkada tanlangan bo'lishi kerak.
    """
    results, _ = week
    pools = _pools(cadets)
    pool_of = {cid: key for key, ids in pools.items() for cid in ids}
    served: Counter = Counter()
    for r in results:
        today = [a.cadet_id for a in r.filled]
        for key, ids in pools.items():
            chosen = [cid for cid in today if pool_of[cid] == key]
            if any(served[cid] >= 1 for cid in chosen):
                not_yet = {cid for cid in ids if served[cid] == 0}
                assert not_yet <= set(chosen), f"{r.day} {key}: turmaganlar qoldi {not_yet - set(chosen)}"
        served.update(today)
    # hafta oxirida hamma kamida bir marta turgan
    assert all(served[c.id] >= 1 for c in cadets)


def test_nobody_two_days_in_a_row(week):
    results, _ = week
    for prev, cur in zip(results, results[1:]):
        assert not {a.cadet_id for a in prev.filled} & {a.cadet_id for a in cur.filled}


def test_week_fairness_min_max_difference_at_most_one(week, cadets):
    results, _ = week
    counts = Counter(a.cadet_id for r in results for a in r.filled)
    for key, ids in _pools(cadets).items():
        values = [counts[cid] for cid in ids]
        assert max(values) - min(values) <= 1, f"{key}: {values}"


def test_two_weeks_fairness_and_no_post_repeat_streaks(cadets):
    """Ikki hafta (2-kurs haftalari 14 kun oralig'ida): adolat saqlanadi."""
    first, history = simulate(cadets, WEEK_START, 7)
    second, history = simulate(cadets, WEEK_START + dt.timedelta(days=14), 7, history=history)
    counts = Counter(r.cadet_id for r in history)
    for key, ids in _pools(cadets).items():
        values = [counts[cid] for cid in ids]
        assert max(values) - min(values) <= 1, f"{key}: {values}"
    # ikkinchi hafta ham to'liq va ogohlantirishsiz
    assert all(len(r.filled) == 20 and not r.warnings for r in second)


# ---------------------------------------------------------------------------
# Cheklovlar
# ---------------------------------------------------------------------------


def test_absent_cadet_is_not_selected(cadets):
    noj1_group = INITIAL_ROTATION["noj1"]
    target = next(c for c in cadets if c.group == noj1_group and c.gender == MALE)
    girl = next(c for c in cadets if c.gender == FEMALE)
    absences = [
        Absence(cadet_id=target.id, start=WEEK_START, end=WEEK_START + dt.timedelta(days=6), reason="kasal"),
        Absence(cadet_id=girl.id, start=WEEK_START, end=WEEK_START + dt.timedelta(days=6), reason="tatil"),
    ]
    results, _ = simulate(cadets, WEEK_START, 7, absences=absences)
    chosen = {a.cadet_id for r in results for a in r.filled}
    assert target.id not in chosen
    assert girl.id not in chosen


def test_inactive_cadet_is_not_selected(cadets):
    target = next(c for c in cadets if c.group == INITIAL_ROTATION["noj1"] and c.gender == MALE)
    modified = [Cadet(**{**c.__dict__, "active": False}) if c.id == target.id else c for c in cadets]
    results, _ = simulate(modified, WEEK_START, 7)
    assert target.id not in {a.cadet_id for r in results for a in r.filled}


def test_slot_left_empty_with_warning_when_only_yesterdays_cadets_remain():
    """Kecha turganlardan boshqa odam qolmasa — o'rin bo'sh qoladi va ogohlantirish chiqadi."""
    groups = ["G1", "G2", "G3", "G4", "G5", "G6"]
    cadets = []
    cid = 0
    for g in groups:
        for _ in range(5):  # har guruhda atigi 5 o'g'il
            cid += 1
            cadets.append(Cadet(id=cid, last_name=f"K{cid}", first_name="A", group=g, gender=MALE))
    for _ in range(6):
        cid += 1
        cadets.append(Cadet(id=cid, last_name=f"Q{cid}", first_name="B", group="G1", gender=FEMALE))
    day1 = dt.date(2026, 9, 13)
    rotation = dict(zip(ROTATION_CHAIN, groups))  # G2 -> noj1 (4 kishi)
    r1 = generate_day(day1, cadets, [], initial_rotation=rotation)
    # Ertasiga G2 2-NO'J ga o'tadi (3 kishi kerak), lekin 4 tasi kecha turgan — faqat 1 kishi qolgan
    r2 = generate_day(day1 + dt.timedelta(days=1), cadets, r1.to_records())
    noj2 = [a for a in r2.assignments if a.slot.post == "noj2"]
    assert r2.group_by_post["noj2"] == "G2"
    assert sum(1 for a in noj2 if a.cadet_id is not None) == 1
    assert sum(1 for s in r2.empty_slots if s.post == "noj2") == 2
    assert noj2[0].slot.role == ROLE_DUTY and noj2[0].cadet_id is not None, "bo'sh qoladigani posbon"
    assert any("2-NO‘J" in w and "G2" in w for w in r2.warnings)
    # Patrul ham shunday: G5 kecha O'quv binosida 2 kishi bergan, 4 kishi kerak — 3 kishi qolgan
    assert sum(1 for s in r2.empty_slots if s.post == "patrul") == 1
    assert len(r2.warnings) == len({s.post for s in r2.empty_slots})
    yesterday = {a.cadet_id for a in r1.filled}
    assert not yesterday & {a.cadet_id for a in r2.filled}


# ---------------------------------------------------------------------------
# Lavozimlar
# ---------------------------------------------------------------------------


def test_assign_roles_avoids_repeating_last_role():
    slots = POSTS_BY_CODE["noj2"].slots  # navbatchi, posbon, posbon
    day = dt.date(2026, 9, 20)
    history = History(
        [
            Record(day=dt.date(2026, 9, 14), cadet_id=1, post="oquv", role=ROLE_DUTY, group="G"),
            Record(day=dt.date(2026, 9, 15), cadet_id=2, post="oquv", role=ROLE_GUARD, group="G"),
            Record(day=dt.date(2026, 9, 16), cadet_id=3, post="noj2", role=ROLE_GUARD, group="G"),
        ],
        before=day,
    )
    result = dict((cid, slot.role) for slot, cid in assign_roles([1, 2, 3], slots, history))
    assert result[1] == ROLE_GUARD, "kecha navbatchi bo'lgan bugun navbatchi bo'lmaydi"
    assert result[1] != ROLE_DUTY


def test_roles_rotate_in_simulation(week):
    """Bir haftada hech kim ketma-ket ikki naryadda bir xil 'navbatchi' lavozimini olmaydi (imkon bo'lsa)."""
    _, history = week
    by_cadet: dict[int, list[Record]] = {}
    for r in sorted(history, key=lambda r: r.day):
        by_cadet.setdefault(r.cadet_id, []).append(r)
    repeats = sum(
        1 for recs in by_cadet.values() for a, b in zip(recs, recs[1:]) if a.role == b.role == ROLE_DUTY
    )
    assert repeats == 0


# ---------------------------------------------------------------------------
# Determinizm
# ---------------------------------------------------------------------------


def test_same_input_same_output(cadets):
    a, _ = simulate(cadets, WEEK_START, 7)
    b, _ = simulate(list(reversed(cadets)), WEEK_START, 7)
    assert [[(x.slot, x.cadet_id) for x in r.assignments] for r in a] == [
        [(x.slot, x.cadet_id) for x in r.assignments] for r in b
    ]


# ---------------------------------------------------------------------------
# Ismlar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "last, first, expected",
    [
        ("Sa'dullayev", "Behro'z", "Sa’dullayev B"),
        ("Shavkatov", "Shaxzod", "Shavkatov Sh"),
        ("G‘ayratov", "G‘iyosiddin", "G‘ayratov G‘"),
        ("Mexmonov", "Shoxrux", "Mexmonov Sh"),
        ("Umirov", "Yashin", "Umirov Y"),
        ("Tursunov", "O'tkir", "Tursunov O‘"),
        ("Botirov", "Chingiz", "Botirov Ch"),
    ],
)
def test_short_name(last, first, expected):
    assert short_name(last, first) == expected


def test_normalize_apostrophes():
    assert normalize_apostrophes("o'g'li") == "o‘g‘li"
    assert normalize_apostrophes("o‘g‘li Ma'ruf A`zamov") == "o‘g‘li Ma’ruf A’zamov"
    assert normalize_apostrophes("Dástan ulí uǵli") == "Dástan ulí uǵli"
    assert first_letter("") == ""


def test_roster_matches_claude_md(cadets):
    # To'liq ro'yxat: 87 o'g'il / 13 qiz (CLAUDE.md 2-bo'lim)
    import json

    from .conftest import ROSTER_PATH

    full = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    assert (sum(c["gender"] == MALE for c in full), sum(c["gender"] == FEMALE for c in full)) == (87, 13)
    assert sum(bool(c.get("duty_exempt")) for c in full) == 9
    # Naryadga chiqadiganlar (nomzodlar hovuzi): 9 ta komandir va kurs lavozimidagi ozod
    expected = {"YuP-125": (11, 2), "BI-225": (12, 3), "BI-325": (12, 2), "BI-425": (14, 2), "BI-525": (16, 0), "BI-625": (13, 4)}
    for group, (boys, girls) in expected.items():
        assert sum(1 for c in cadets if c.group == group and c.gender == MALE) == boys
        assert sum(1 for c in cadets if c.group == group and c.gender == FEMALE) == girls
