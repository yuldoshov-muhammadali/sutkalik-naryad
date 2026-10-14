"""Sutkalik naryad taqsimlash algoritmi (CLAUDE.md 4- va 10-bo'limlar).

Ikki daraja:
  1) rotate_groups — qaysi guruh qaysi o'g'il bolalar joyiga (aylanish zanjiri);
  2) pick_cadets + assign_roles — guruh ichidan kim va qaysi lavozimga.
Qizlar guruhga bog'lanmaydi: 13 qiz bitta umumiy navbat.

Algoritm faqat tasdiqlangan sutkalar tarixini (Record) oladi va bitta sutka
qoralamasini (DayResult) qaytaradi. Natija to'liq deterministik.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
from collections.abc import Iterable, Mapping, Sequence

from .config import DUTY_START_TIME, FEMALE_POST, MALE_POSTS, POSTS, POSTS_BY_CODE, ROTATION_CHAIN
from .models import (
    FEMALE,
    MALE,
    Absence,
    Assignment,
    Cadet,
    CandidateScore,
    DayResult,
    PickResult,
    Record,
    Slot,
)

# Chiqarib tashlash sabablari (tushuntirish jadvallari uchun)
EXCLUDED_INACTIVE = "faol emas"
EXCLUDED_ABSENT = "sababli yo‘q"
EXCLUDED_YESTERDAY = "kecha naryadda bo‘lgan"
EXCLUDED_TAKEN = "bugun boshqa o‘ringa qo‘yilgan"


class AllocationError(ValueError):
    """Kirish ma'lumotlari noto'g'ri bo'lganda (masalan, boshlang'ich taqsimot yo'q)."""


# ---------------------------------------------------------------------------
# Vaqt: sutka va hafta
# ---------------------------------------------------------------------------


def week_start(day: dt.date) -> dt.date:
    """Sutka tegishli 2-kurs haftasi boshlangan yakshanba sanasi.

    Sutka `day` kuni 18:00 da boshlanadi. Hafta yakshanba 18:00 dan keyingi
    yakshanba 18:00 gacha, shuning uchun yakshanba sanali sutka yangi haftaning
    birinchi sutkasi bo'ladi.
    """
    # Python: dushanba=0 … yakshanba=6
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)


def week_bounds(day: dt.date) -> tuple[dt.datetime, dt.datetime]:
    """Sutka tushgan 2-kurs haftasining boshlanishi va tugashi (yakshanba 18:00 – yakshanba 18:00)."""
    start = dt.datetime.combine(week_start(day), DUTY_START_TIME)
    return start, start + dt.timedelta(days=7)


def duty_bounds(day: dt.date) -> tuple[dt.datetime, dt.datetime]:
    """Sutkaning boshlanishi va tugashi (18:00 – ertasi 18:00)."""
    start = dt.datetime.combine(day, DUTY_START_TIME)
    return start, start + dt.timedelta(days=1)


# ---------------------------------------------------------------------------
# Tarix bo'yicha yordamchi hisoblar
# ---------------------------------------------------------------------------


class History:
    """Tasdiqlangan yozuvlar ustidan tez so'rovlar (faqat `before` sanasidan oldingilar)."""

    def __init__(self, records: Iterable[Record], before: dt.date):
        self.before = before
        self.records: list[Record] = sorted(
            (r for r in records if r.day < before), key=lambda r: (r.day, r.post, r.position)
        )
        self.by_cadet: dict[int, list[Record]] = {}
        for r in self.records:
            self.by_cadet.setdefault(r.cadet_id, []).append(r)

    def of(self, cadet_id: int) -> list[Record]:
        return self.by_cadet.get(cadet_id, [])

    def last(self, cadet_id: int) -> Record | None:
        recs = self.of(cadet_id)
        return recs[-1] if recs else None

    def on_day(self, day: dt.date) -> list[Record]:
        return [r for r in self.records if r.day == day]

    def last_day(self) -> dt.date | None:
        return self.records[-1].day if self.records else None


def _tiebreak(day: dt.date, cadet_id: int) -> str:
    """Sana + kursant asosidagi deterministik "tasodif" (alifbo tartibi emas)."""
    return hashlib.sha256(f"{day.isoformat()}|{cadet_id}".encode()).hexdigest()


def score_candidate(cadet: Cadet, post_code: str, day: dt.date, history: History) -> CandidateScore:
    """CLAUDE.md 4-D saralash kalitining qiymatlari."""
    recs = history.of(cadet.id)
    this_week = week_start(day)
    last = recs[-1] if recs else None
    last_is_same = last is not None and last.post == post_code
    return CandidateScore(
        cadet_id=cadet.id,
        week_count=sum(1 for r in recs if week_start(r.day) == this_week),
        total=len(recs),
        penalty=1 if last_is_same else 0,
        last_is_same_post=last_is_same,
        post_count=sum(1 for r in recs if r.post == post_code),
        last_day=last.day if last else None,
        tiebreak=_tiebreak(day, cadet.id),
    )


def _is_absent(cadet_id: int, day: dt.date, absences: Iterable[Absence]) -> bool:
    return any(a.cadet_id == cadet_id and a.covers(day) for a in absences)


# ---------------------------------------------------------------------------
# a) Guruhlar aylanishi
# ---------------------------------------------------------------------------


def rotate_groups(
    groups: Sequence[str],
    history: Iterable[Record] | History,
    day: dt.date | None = None,
    initial_rotation: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Bugungi sutka uchun o'g'il bolalar joyi -> guruh taqsimoti.

    Har guruh oxirgi 2-kurs sutkasidagi joyidan zanjirdagi keyingi joyga o'tadi
    (Markaz → 1-NO‘J → … → Patrul → Markaz). Oxirgi sutka oldingi haftada bo'lsa
    ham zanjir davom etadi.

    Tarixda o'g'il bolalar yozuvi bo'lmasa, `initial_rotation` (joy kodi -> guruh)
    aynan shu sutkaning taqsimoti sifatida qabul qilinadi (admin qo'lda kiritadi).
    """
    groups = list(groups)
    if len(groups) != len(ROTATION_CHAIN) or len(set(groups)) != len(groups):
        raise AllocationError(f"Aynan {len(ROTATION_CHAIN)} ta turli guruh kerak, berildi: {groups}")

    if isinstance(history, History):
        hist = history
    else:
        hist = History(history, before=day or dt.date.max)

    male_codes = set(ROTATION_CHAIN)
    male_records = [r for r in hist.records if r.post in male_codes]

    if not male_records:
        if initial_rotation is None:
            raise AllocationError("Tarix bo‘sh: birinchi sutka uchun boshlang‘ich taqsimot (initial_rotation) kerak")
        mapping = dict(initial_rotation)
        _validate_mapping(mapping, groups)
        return mapping

    last_day = male_records[-1].day
    previous = previous_group_by_post([r for r in male_records if r.day == last_day], groups)
    # Kechagi i-joydagi guruh bugun (i+1)-joyga o'tadi
    n = len(ROTATION_CHAIN)
    mapping = {ROTATION_CHAIN[(i + 1) % n]: previous[code] for i, code in enumerate(ROTATION_CHAIN)}
    _validate_mapping(mapping, groups)
    return mapping


def previous_group_by_post(day_records: Iterable[Record], groups: Sequence[str]) -> dict[str, str]:
    """Bir sutka yozuvlaridan joy -> guruh taqsimotini tiklaydi.

    Agar bitta joy butunlay bo'sh qolgan bo'lsa (yozuvi yo'q), u qolgan yagona
    guruhga tegishli deb olinadi.
    """
    mapping: dict[str, str] = {}
    for r in day_records:
        if r.post not in ROTATION_CHAIN:
            continue
        if r.post in mapping and mapping[r.post] != r.group:
            raise AllocationError(f"{r.day}: {r.post} joyida bir nechta guruh bor ({mapping[r.post]}, {r.group})")
        mapping[r.post] = r.group
    missing_posts = [c for c in ROTATION_CHAIN if c not in mapping]
    missing_groups = [g for g in groups if g not in mapping.values()]
    if len(missing_posts) == 1 and len(missing_groups) == 1:
        mapping[missing_posts[0]] = missing_groups[0]
    if len(mapping) != len(ROTATION_CHAIN):
        raise AllocationError(f"Oxirgi sutkadan guruh taqsimotini tiklab bo‘lmadi: {mapping}")
    return mapping


def _validate_mapping(mapping: Mapping[str, str], groups: Sequence[str]) -> None:
    if set(mapping) != set(ROTATION_CHAIN):
        raise AllocationError(f"Taqsimotda barcha 6 ta o‘g‘il joyi bo‘lishi kerak: {sorted(mapping)}")
    if sorted(mapping.values()) != sorted(groups):
        raise AllocationError(f"Har guruh aynan bitta joy olishi kerak: {dict(mapping)}")


# ---------------------------------------------------------------------------
# c) Guruh (yoki qizlar hovuzi) ichidan tanlash
# ---------------------------------------------------------------------------


def pick_cadets(
    pool: Sequence[Cadet],
    post_code: str,
    need: int,
    day: dt.date,
    history: History,
    absences: Iterable[Absence] = (),
    taken: Iterable[int] = (),
) -> PickResult:
    """Hovuzdan `need` ta kursant tanlaydi.

    Qat'iy cheklovlar: faol emas, sababli yo'q, kecha naryadda bo'lgan va bugun
    boshqa o'ringa qo'yilgan kursantlar olinmaydi. Nomzod yetmasa, kamroq
    tanlanadi (bo'sh o'rinni admin qo'lda to'ldiradi).

    Saralash kaliti (CLAUDE.md 4-D): haftadagi soni → jami (+1 jarima, agar oxirgi
    naryadi shu joy bo'lsa) → oxirgi joyi shu joymi → shu joydagi soni → oxirgi
    naryad sanasi (uzoq dam olgan oldin) → deterministik tasodif.
    """
    absences = list(absences)
    taken = set(taken)
    yesterday_ids = {r.cadet_id for r in history.on_day(day - dt.timedelta(days=1))}

    excluded: dict[int, str] = {}
    eligible: list[CandidateScore] = []
    for cadet in pool:
        if not cadet.active:
            excluded[cadet.id] = EXCLUDED_INACTIVE
        elif _is_absent(cadet.id, day, absences):
            excluded[cadet.id] = EXCLUDED_ABSENT
        elif cadet.id in taken:
            excluded[cadet.id] = EXCLUDED_TAKEN
        elif cadet.id in yesterday_ids:
            excluded[cadet.id] = EXCLUDED_YESTERDAY
        else:
            eligible.append(score_candidate(cadet, post_code, day, history))

    ranking = tuple(sorted(eligible, key=lambda s: s.sort_key))
    chosen = tuple(s.cadet_id for s in ranking[:need])
    return PickResult(chosen=chosen, ranking=ranking, excluded=excluded)


# ---------------------------------------------------------------------------
# d) Lavozimlarni taqsimlash
# ---------------------------------------------------------------------------


def assign_roles(cadet_ids: Sequence[int], slots: Sequence[Slot], history: History) -> list[tuple[Slot, int]]:
    """Tanlangan kursantlarni joy o'rinlariga eng adolatli tarzda qo'yadi.

    Barcha almashtirishlar (ko'pi bilan 4! = 24) ko'rib chiqiladi va quyidagi
    kalit bo'yicha eng kichigi olinadi:
      1) oxirgi lavozimi takrorlanadigan kursantlar soni;
      2) har kimning shu joydagi shu lavozimda turgan sonlari yig'indisi;
      3) har kimning umuman shu lavozimda turgan sonlari yig'indisi.
    Teng bo'lsa — tanlanish tartibidagi birinchi variant (deterministik).

    Kursant o'rinlardan kam bo'lsa, oxirgi o'rinlar (odatda posbon) bo'sh qoladi.
    """
    slots = list(slots)[: len(cadet_ids)]
    if not cadet_ids:
        return []

    def cost(cid: int, slot: Slot) -> tuple[int, int, int]:
        recs = history.of(cid)
        last = recs[-1] if recs else None
        repeat = 1 if last is not None and last.role == slot.role else 0
        same_post_role = sum(1 for r in recs if r.post == slot.post and r.role == slot.role)
        same_role = sum(1 for r in recs if r.role == slot.role)
        return repeat, same_post_role, same_role

    costs = {(cid, s.position): cost(cid, s) for cid in cadet_ids for s in slots}
    best: tuple | None = None
    best_perm: tuple[int, ...] = ()
    for perm in itertools.permutations(cadet_ids):
        total = tuple(sum(costs[(cid, s.position)][k] for cid, s in zip(perm, slots)) for k in range(3))
        if best is None or total < best:
            best, best_perm = total, perm
    return list(zip(slots, best_perm))


# ---------------------------------------------------------------------------
# e) Butun sutka
# ---------------------------------------------------------------------------


def generate_day(
    day: dt.date,
    cadets: Sequence[Cadet],
    history: Iterable[Record],
    absences: Iterable[Absence] = (),
    initial_rotation: Mapping[str, str] | None = None,
) -> DayResult:
    """Bitta sutka qoralamasini tuzadi.

    - 6 ta o'g'il bolalar joyi: guruhlar aylanish zanjiri bo'yicha, har joy bitta
      guruhdan to'liq;
    - Qizlar yotoqxonasi: 13 qizning umumiy navbatidan;
    - bir kursant bir sutkada faqat bitta o'rinda;
    - nomzod yetmasa o'rin bo'sh qoladi va ogohlantirish yoziladi.
    """
    absences = list(absences)
    hist = History(history, before=day)
    by_id = {c.id: c for c in cadets}
    groups = sorted({c.group for c in cadets if c.gender == MALE})

    group_by_post = rotate_groups(groups, hist, day=day, initial_rotation=initial_rotation)

    taken: set[int] = set()
    assignments: dict[tuple[str, int], Assignment] = {}
    warnings: list[str] = []
    picks: dict[str, PickResult] = {}

    jobs: list[tuple[str, list[Cadet], str | None]] = []
    for post in MALE_POSTS:
        group = group_by_post[post.code]
        pool = [c for c in cadets if c.gender == MALE and c.group == group]
        jobs.append((post.code, pool, group))
    jobs.append((FEMALE_POST.code, [c for c in cadets if c.gender == FEMALE], None))

    for post_code, pool, group in jobs:
        post = POSTS_BY_CODE[post_code]
        pick = pick_cadets(pool, post_code, post.size, day, hist, absences, taken)
        picks[post_code] = pick
        taken.update(pick.chosen)
        for slot, cid in assign_roles(pick.chosen, post.slots, hist):
            assignments[(post_code, slot.position)] = Assignment(slot=slot, cadet_id=cid, group=by_id[cid].group)
        if len(pick.chosen) < post.size:
            missing = post.size - len(pick.chosen)
            who = f"{group} guruhida" if group else "Qizlar navbatida"
            reasons = _summarize_exclusions(pick.excluded)
            warnings.append(
                f"{post.name}: {who} munosib nomzod yetmadi — {missing} ta o‘rin bo‘sh qoldi"
                f" ({reasons}). O‘rinni admin (kurs boshlig‘i) qo‘lda to‘ldiradi."
            )

    ordered: list[Assignment] = []
    for post in POSTS:
        for slot in post.slots:
            ordered.append(assignments.get((post.code, slot.position), Assignment(slot=slot, cadet_id=None, group=None)))

    return DayResult(
        day=day,
        week_start=week_start(day),
        group_by_post=group_by_post,
        assignments=ordered,
        warnings=warnings,
        picks=picks,
    )


def _summarize_exclusions(excluded: Mapping[int, str]) -> str:
    if not excluded:
        return "hovuzda kursant yo‘q"
    counts: dict[str, int] = {}
    for reason in excluded.values():
        counts[reason] = counts.get(reason, 0) + 1
    return ", ".join(f"{reason}: {n}" for reason, n in counts.items())
