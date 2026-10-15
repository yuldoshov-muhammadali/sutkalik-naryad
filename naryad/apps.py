from django.apps import AppConfig
from django.contrib.admin import apps as admin_apps
from django.utils.translation import gettext_lazy as _lazy


class NaryadConfig(AppConfig):
    default = True
    default_auto_field = "django.db.models.BigAutoField"
    name = "naryad"
    verbose_name = _lazy("Sutkalik naryad")


class NaryadAdminConfig(admin_apps.AdminConfig):
    """django.contrib.admin o'rniga: standart sayt — NaryadAdminSite (faqat admin roli kiradi)."""

    default = False
    default_site = "naryad.admin_site.NaryadAdminSite"
