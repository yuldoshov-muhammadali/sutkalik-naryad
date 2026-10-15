"""Admin panel sayti: faqat admin roli va superuser kiradi (CLAUDE.md 10-bo'lim, 19-band)."""

from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _lazy

from .auth import AdminLoginForm


class NaryadAdminSite(AdminSite):
    site_header = _lazy("Sutkalik naryad — boshqaruv paneli")
    site_title = _lazy("Sutkalik naryad")
    index_title = _lazy("2-kurs sutkalik naryadlari")
    login_form = AdminLoginForm
    site_url = "/"

    def has_permission(self, request):
        user = request.user
        return bool(user.is_active and (user.is_superuser or getattr(user, "role", None) == "admin"))
