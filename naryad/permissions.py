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

ROLE_TITLES = {
    ADMIN: _lazy("Admin (kurs boshlig‘i)"),
    CADET: _lazy("Kursant"),
}

ALL = frozenset({ADMIN, CADET})
ADMIN_ONLY = frozenset({ADMIN})

# amal -> (tavsif, ruxsat etilgan rollar)
PERMISSIONS: dict[str, tuple[str, frozenset[str]]] = {
    "home.view": (_lazy("Bosh sahifa (rolga qarab)"), ALL),
    "account.password_change": (_lazy("O‘z parolini almashtirish"), ALL),
    # 14-bosqich: kursant boshqa kursantlarning ro'yxatini (sutka sahifalari, PDF) ko'rmaydi — faqat o'z naryadi
    "day.view_approved": (_lazy("Tasdiqlangan sutkalarni ko‘rish"), ADMIN_ONLY),
    "history.own": (_lazy("O‘z kartochkasi va naryad tarixini ko‘rish"), frozenset({CADET})),
    "week.view": (_lazy("2-kurs haftalari va sutkalar holatini ko‘rish"), ADMIN_ONLY),
    "week.open": (_lazy("2-kurs haftasini ochish"), ADMIN_ONLY),
    "day.view_draft": (_lazy("Qoralama sutkalarni ko‘rish"), ADMIN_ONLY),
    "day.generate": (_lazy("Sutka qoralamasini tuzish (ro‘yxatni dastur avtomatik tuzadi)"), ADMIN_ONLY),
    "day.edit": (_lazy("Qoralamani qo‘lda tuzatish (sabab majburiy, jurnalga yoziladi)"), ADMIN_ONLY),
    "day.approve": (_lazy("Sutkani tasdiqlash"), ADMIN_ONLY),
    "day.reopen": (_lazy("Tasdiqlangan sutkani qayta ochish (sabab majburiy)"), ADMIN_ONLY),
    "absence.manage": (_lazy("Sababli yo‘qliklarni (kasal, ta’til) kiritish"), ADMIN_ONLY),
    "penalty.manage": (_lazy("Zalyotchiklar: navbatdan tashqari jazo naryadini kiritish va bekor qilish"), ADMIN_ONLY),
    "history.all": (_lazy("Har qanday kursant kartochkasi, tarixi va statistika"), ADMIN_ONLY),
    "pdf.export": (_lazy("PDF yuklab olish va chop etish"), ADMIN_ONLY),
    "cadets.view": (_lazy("Kursantlar ro‘yxatini ko‘rish (filtr, qidiruv)"), ADMIN_ONLY),
    "cadets.manage": (_lazy("Kursant qo‘shish, tahrirlash, faolsizlantirish, Excel import, akkauntlar"), ADMIN_ONLY),
    "settings.manage": (_lazy("Sozlamalar va boshlang‘ich taqsimot"), ADMIN_ONLY),
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
