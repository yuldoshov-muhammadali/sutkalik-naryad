"""Rollar va ruxsatlar — yagona jadval (docs/05-rollar.md shu jadvaldan).

Har bir amal (kalit) uchun: o'zbekcha tavsif va ruxsat etilgan rollar.
Superuser har doim admin hisoblanadi. Yangi sahifa qo'shilganda shu jadvalga
amal qo'shiladi va sahifa `role_required("amal")` yoki `RoleRequiredMixin`
bilan himoyalanadi.
"""

from __future__ import annotations

from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy

ADMIN = "admin"
CADET = "cadet"
COMMANDER = "commander"  # guruh komandiri (19-bosqich): kursant imkoniyatlari + “Mening guruhim” (faqat ko'rish)

ROLE_TITLES = {
    ADMIN: _lazy("Admin (kurs boshlig‘i)"),
    CADET: _lazy("Kursant"),
    COMMANDER: _lazy("Guruh komandiri"),
}

ALL = frozenset({ADMIN, CADET, COMMANDER})
CADETS = frozenset({CADET, COMMANDER})  # komandir ham kursant: o'z kartochkasi, hujjatlari
ADMIN_ONLY = frozenset({ADMIN})

# amal -> (tavsif, ruxsat etilgan rollar)
PERMISSIONS: dict[str, tuple[str, frozenset[str]]] = {
    "home.view": (_lazy("Bosh sahifa (rolga qarab)"), ALL),
    "account.password_change": (_lazy("O‘z parolini almashtirish"), ALL),
    # 16-bosqich: kursant yana tasdiqlangan sutkalarni (faqat o'qish uchun) ko'radi; qoralama — hech qachon
    "day.view_approved": (_lazy("Tasdiqlangan sutkalarni ko‘rish (kursant — faqat o‘qish uchun)"), ALL),
    "history.own": (_lazy("O‘z kartochkasi va naryad tarixini ko‘rish"), CADETS),
    "group.view": (_lazy("Mening guruhim: o‘z guruhi kursantlarining tasdiqlangan naryadlari va “kasal, sana–sana” (faqat ko‘rish)"), frozenset({COMMANDER})),
    "week.view": (_lazy("2-kurs haftalari va sutkalar holatini ko‘rish"), ADMIN_ONLY),
    "week.open": (_lazy("2-kurs haftasini ochish"), ADMIN_ONLY),
    "day.view_draft": (_lazy("Qoralama sutkalarni ko‘rish"), ADMIN_ONLY),
    "day.generate": (_lazy("Sutka qoralamasini tuzish (ro‘yxatni dastur avtomatik tuzadi)"), ADMIN_ONLY),
    "day.edit": (_lazy("Qoralamani qo‘lda tuzatish (sabab majburiy, jurnalga yoziladi)"), ADMIN_ONLY),
    "day.approve": (_lazy("Sutkani tasdiqlash"), ADMIN_ONLY),
    "day.reopen": (_lazy("Tasdiqlangan sutkani qayta ochish (sabab majburiy)"), ADMIN_ONLY),
    "absence.manage": (_lazy("Sababli yo‘qliklarni (kasal, ta’til) kiritish"), ADMIN_ONLY),
    "sick.manage": (_lazy("Kasallar ro‘yxati: kasallikni kiritish, tahrirlash, muddatni uzaytirish (tavsif bilan), hujjat rasmlari"), ADMIN_ONLY),
    "documents.own": (_lazy("O‘z kasallik hujjatlarini (rasmlarini) ko‘rish — faqat ko‘rish"), CADETS),
    "penalty.group": (_lazy("O‘z guruhi kursantiga zalyot kiritish va o‘z guruhi zalyotlarini ko‘rish (tahrir va bekor qilish — yo‘q)"), frozenset({COMMANDER})),
    "penalty.manage": (_lazy("Zalyotchiklar: jazo naryadini kiritish, tahrirlash, bekor qilish, ko‘rib chiqish va zalyot hisobi"), ADMIN_ONLY),
    "history.all": (_lazy("Har qanday kursant kartochkasi, tarixi va statistika"), ADMIN_ONLY),
    "pdf.export": (_lazy("PDF yuklab olish va chop etish (kursant — faqat tasdiqlangan sutkalar)"), ALL),
    "cadets.view": (_lazy("Kursantlar ro‘yxatini ko‘rish (filtr, qidiruv)"), ADMIN_ONLY),
    "cadets.manage": (_lazy("Kursant qo‘shish, tahrirlash, faolsizlantirish, Excel import, akkauntlar"), ADMIN_ONLY),
    "settings.manage": (_lazy("Sozlamalar, boshlang‘ich taqsimot va sinov ma’lumotlarini tozalash"), ADMIN_ONLY),
    "admin_panel": (_lazy("Django boshqaruv paneli (/admin/)"), ADMIN_ONLY),
}


def user_role(user) -> str | None:
    if not getattr(user, "is_authenticated", False) or not user.is_active:
        return None
    if user.is_superuser:
        return ADMIN
    return getattr(user, "role", None)


def can(user, action: str) -> bool:
    if action not in PERMISSIONS:
        raise KeyError(f"Ruxsatlar jadvalida yo‘q amal: {action}")
    role = user_role(user)
    return role is not None and role in PERMISSIONS[action][1]


def check(request, action: str) -> None:
    """Ruxsat bo'lmasa: mehmon — login sahifasiga, boshqalar — 403."""
    if not request.user.is_authenticated:
        raise _LoginRequired
    if not can(request.user, action):
        raise PermissionDenied(_("Bu sahifa uchun ruxsat yo‘q (%(action)s).") % {"action": PERMISSIONS[action][0]})


class _LoginRequired(Exception):
    pass


def role_required(action: str):
    """Funksiya ko'rinishidagi view uchun dekorator."""
    if action not in PERMISSIONS:
        raise KeyError(f"Ruxsatlar jadvalida yo‘q amal: {action}")

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            try:
                check(request, action)
            except _LoginRequired:
                return redirect_to_login(request.get_full_path())
            return view(request, *args, **kwargs)

        wrapper.required_action = action
        return wrapper

    return decorator


class RoleRequiredMixin:
    """Klass ko'rinishidagi view uchun: `permission = "amal"`."""

    permission: str = ""

    def dispatch(self, request, *args, **kwargs):
        try:
            check(request, self.permission)
        except _LoginRequired:
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)


def permissions_for(user) -> dict[str, bool]:
    """Shablonlar uchun: {"day_approve": True, ...}."""
    return {action.replace(".", "_"): can(user, action) for action in PERMISSIONS}
