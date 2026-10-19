from django.apps import AppConfig
from django.conf import settings
from django.contrib.admin import apps as admin_apps


class NaryadConfig(AppConfig):
    default = True
    default_auto_field = "django.db.models.BigAutoField"
    name = "naryad"
    verbose_name = settings.SITE_NAME  # platforma nomi (18-bosqich)


class NaryadAdminConfig(admin_apps.AdminConfig):
    """django.contrib.admin o'rniga: standart sayt — NaryadAdminSite (faqat admin roli kiradi)."""

    default = False
    default_site = "naryad.admin_site.NaryadAdminSite"
