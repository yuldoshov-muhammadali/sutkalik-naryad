"""Testlar uchun sozlamalar: maxfiy kalit talab qilinmaydi, parollar tez xeshlanadi."""

import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-only-secret-key")

from .settings import *  # noqa: E402,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES["staticfiles"]["BACKEND"] = "django.contrib.staticfiles.storage.StaticFilesStorage"  # noqa: F405
WHITENOISE_AUTOREFRESH = True  # testlarda collectstatic qilinmaydi
