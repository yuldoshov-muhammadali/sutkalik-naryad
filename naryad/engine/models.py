"""Algoritm uchun ma'lumot tuzilmalari (faqat standart kutubxona).

Bu modul Django'ga bog'liq emas: Django modellari keyingi bosqichda shu
dataclass'larga o'giriladi va algoritmga beriladi.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

MALE = "M"
FEMALE = "F"

# Lavozimlar
ROLE_DUTY = "navbatchi"
ROLE_ASSISTANT = "navbatchi_yordamchisi"
ROLE_GUARD = "posbon"

# Naryad turi (15-bosqich): oddiy navbat yoki navbatdan tashqari (jazo) naryadi
KIND_NORMAL = "normal"
KIND_PENALTY = "penalty"

ROLE_TITLES = {
    ROLE_DUTY: "Navbatchi",
    ROLE_ASSISTANT: "Navbatchi yordamchisi",
    ROLE_GUARD: "Posbon",
}


@dataclass(frozen=True)
class Slot:
    """Joy ichidagi bitta o'rin (lavozim)."""

    post: str  # joy kodi, masalan "noj1"
    position: int  # joy ichidagi tartib: 1, 2, 3, 4
    role: str  # ROLE_DUTY / ROLE_ASSISTANT / ROLE_GUARD
    pdf_label: str  # PDF'dagi qator yozuvi
    show_label: bool = True  # Patrulda faqat 1-qatorda yozuv ko'rsatiladi


@dataclass(frozen=True)
class Post:
    """Navbatchilik joyi."""

    code: str
    name: str
    section_title: str
    gender: str  # MALE / FEMALE
    display_order: int  # PDF'dagi tartib
    rotation_index: int | None  # aylanish zanjiridagi o'rni (qizlar joyida None)
    slots: tuple[Slot, ...]

    @property
    def size(self) -> int:
        return len(self.slots)


@dataclass(frozen=True)
class Cadet:
    """Kursant."""

    id: int
    last_name: str
    first_name: str
    group: str  # guruh kodi, masalan "BI-525"
    gender: str  # MALE / FEMALE
    patronymic: str = ""
    active: bool = True
    short_name: str = ""  # PDF uchun qisqa shakl ("Sa'dullayev B")

    @property
    def display_name(self) -> str:
        return self.short_name or f"{self.last_name} {self.first_name[:1]}"


@dataclass(frozen=True)
class Record:
    """Tarix yozuvi: kim, qachon, qayerda, qaysi lavozimda, qaysi guruhdan.

    Algoritmga faqat tasdiqlangan sutkalarning yozuvlari beriladi.
    """

    day: dt.date  # sutka boshlangan sana (18:00)
    cadet_id: int
    post: str
    role: str
    group: str
    position: int = 0
    kind: str = KIND_NORMAL  # jazo naryadi adolat hisobiga kirmaydi (faqat “kecha turgan” cheklovi uchun)


@dataclass(frozen=True)
class Offender:
    """Faol zalyotchik (15-bosqich): navbatdan tashqari jazo naryadi qarzi bor kursant.

    since — buyruq/tanbeh sanasi (eskisi birinchi), remaining — qolgan jazo naryadlari,
    last_post — oxirgi jazo naryadi joyi (joy navbatma-navbat almashadi).
    """

    cadet_id: int
    since: dt.date
    remaining: int
    last_post: str | None = None


@dataclass(frozen=True)
class Absence:
    """Sababli yo'qlik: start..end sutkalari (ikkala chegara ham ichida)."""

    cadet_id: int
    start: dt.date
    end: dt.date
    reason: str = "kasal"

    def covers(self, day: dt.date) -> bool:
        return self.start <= day <= self.end


@dataclass(frozen=True)
class CandidateScore:
    """Nomzodning saralash kaliti — tushuntirish jadvallari uchun."""

    cadet_id: int
    week_count: int  # shu 2-kurs haftasida necha marta turgan
    total: int  # jami naryadlar soni (jarimasiz)
    penalty: int  # oxirgi naryadi shu joy bo'lsa 1, aks holda 0
    last_is_same_post: bool
    post_count: int  # shu joyda necha marta turgan
    last_day: dt.date | None  # oxirgi naryad sanasi
    tiebreak: str  # deterministik tasodif (sana + kursant)

    @property
    def sort_key(self) -> tuple:
        return (
            self.week_count,
            self.total + self.penalty,
            1 if self.last_is_same_post else 0,
            self.post_count,
            self.last_day or dt.date.min,
            self.tiebreak,
        )


@dataclass(frozen=True)
class PickResult:
    """pick_cadets() natijasi."""

    chosen: tuple[int, ...]  # tanlangan kursantlar id'lari, tanlanish tartibida
    ranking: tuple[CandidateScore, ...]  # barcha munosib nomzodlar, saralangan holda
    excluded: dict[int, str]  # chiqarib tashlanganlar: id -> sabab


@dataclass(frozen=True)
class Assignment:
    """Sutkadagi bitta o'rin va unga qo'yilgan kursant (bo'sh bo'lishi mumkin)."""

    slot: Slot
    cadet_id: int | None
    group: str | None
    kind: str = KIND_NORMAL


@dataclass
class DayResult:
    """Bir sutka natijasi (qoralama)."""

    day: dt.date
    week_start: dt.date
    group_by_post: dict[str, str]  # o'g'il joyi kodi -> guruh kodi
    assignments: list[Assignment]
    warnings: list[str] = field(default_factory=list)
    picks: dict[str, PickResult] = field(default_factory=dict)  # joy kodi -> tanlash tafsiloti

    @property
    def filled(self) -> list[Assignment]:
        return [a for a in self.assignments if a.cadet_id is not None]

    @property
    def empty_slots(self) -> list[Slot]:
        return [a.slot for a in self.assignments if a.cadet_id is None]

    def to_records(self) -> list[Record]:
        """Sutka tasdiqlangach tarixga qo'shiladigan yozuvlar."""
        return [
            Record(
                day=self.day,
                cadet_id=a.cadet_id,
                post=a.slot.post,
                role=a.slot.role,
                group=a.group or "",
                position=a.slot.position,
                kind=a.kind,
            )
            for a in self.filled
        ]
