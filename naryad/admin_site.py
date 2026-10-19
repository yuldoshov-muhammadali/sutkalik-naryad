"""Admin panel sayti: faqat admin roli va superuser kiradi (CLAUDE.md 10-bo'lim, 19-band)."""

from django.conf import settings
from django.contrib.admin import AdminSite
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _lazy

from .auth import AdminLoginForm


class NaryadAdminSite(AdminSite):
    # Platforma nomi settings.SITE_NAME dan (18-bosqich), tarjima qilinmaydi
    site_header = format_lazy("{} — {}", settings.SITE_NAME, _lazy("boshqaruv paneli"))
    site_title = settings.SITE_NAME
    index_title = _lazy("Naryad ma’lumotlari")
    login_form = AdminLoginForm
    site_url = "/"

    def has_permission(self, request):
        user = request.user
        return bool(user.is_active and (user.is_superuser or getattr(user, "role", None) == "admin"))
