"""Django sozlamalari.

Maxfiy kalit, DEBUG va baza manzili muhit o'zgaruvchilaridan (yoki loyiha
ildizidagi .env faylidan) olinadi. Namuna: .env.example.
"""

from __future__ import annotations

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "ha"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", default=False)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-only-insecure-key-change-me"  # faqat lokal ishlab chiqish uchun
    else:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY muhit o‘zgaruvchisi berilmagan (.env.example ga qarang)")

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "naryad.apps.NaryadAdminConfig",  # django.contrib.admin, faqat admin roli kiradi
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "naryad",
]

MIDDLEWARE = [
    "naryad.security.HealthCheckMiddleware",  # /health/ — Host va HTTPS tekshiruvidan oldin
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "naryad.i18n.LanguageMiddleware",  # til: User.language / cookie / o'zbekcha (Accept-Language o'qilmaydi)
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "naryad.auth.ForcePasswordChangeMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "naryad.security.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "naryad.context_processors.ui",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# DATABASE_URL bo'lmasa — SQLite (lokal ishlab chiqish)
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=int(os.environ.get("DJANGO_DB_CONN_MAX_AGE", "60")),
    )
}

AUTH_USER_MODEL = "naryad.User"
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"

# Login urinishlarini cheklash: 5 marta xato → 15 daqiqa blok
LOGIN_MAX_FAILURES = int(os.environ.get("LOGIN_MAX_FAILURES", "5"))
LOGIN_BLOCK_MINUTES = int(os.environ.get("LOGIN_BLOCK_MINUTES", "15"))

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Platforma nomi (18-bosqich, CLAUDE.md 65-band): hamma tilda bir xil, tarjima qilinmaydi.
# Ko'rinadigan joylar uni shu yerdan oladi (kontekst protsessori `site_name`, `{% site_name %}` tegi).
SITE_NAME = "E-NARYAD"

# “Sinov ma'lumotlarini tozalash” oldidan avtomatik zaxira (20-bosqich). Railway'da disk vaqtinchalik — darhol yuklab olinadi.
BACKUP_DIR = Path(os.environ.get("DJANGO_BACKUP_DIR", BASE_DIR / "data" / "zaxira"))

LANGUAGE_CODE = "uz"
# Uch til (13-bosqich): o'zbekcha asosiy. Til faqat foydalanuvchi tanlovi bilan o'zgaradi (naryad/i18n.py)
LANGUAGES = [("uz", "O‘zbekcha"), ("ru", "Русский"), ("en", "English")]
LANGUAGE_COOKIE_NAME = "naryad_til"
LANGUAGE_COOKIE_AGE = 365 * 24 * 60 * 60
LANGUAGE_COOKIE_SAMESITE = "Lax"
LANGUAGE_COOKIE_HTTPONLY = True
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
# Django admin/auth uchun yetishmagan o'zbekcha tarjimalar (python scripts/compile_messages.py)
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Railway / proksi orqasida HTTPS
if env_bool("DJANGO_SECURE_PROXY", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Yuklanadigan fayllar (kursantlar Excel importi): 2 MB dan katta so'rov qabul qilinmaydi
DATA_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 3 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 2000

# Sessiya: brauzer yopilsa ham 12 soat amal qiladi
SESSION_COOKIE_AGE = 12 * 60 * 60
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True  # HTMX tokenni sahifadan oladi (base.html, hx-headers)
X_FRAME_OPTIONS = "DENY"  # PDF'ni chop etish oynasi uchun faqat PDF javobi SAMEORIGIN

# Loglar: konsolga va (DJANGO_LOG_DIR berilsa) faylga — 5 MB dan, 5 ta eski fayl saqlanadi
LOG_LEVEL = os.environ.get("DJANGO_LOG_LEVEL", "INFO")
LOG_DIR = os.environ.get("DJANGO_LOG_DIR", "")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    # PDF kutubxonalarining batafsil INFO yozuvlari loglarni to'ldirmasin
    "loggers": {name: {"level": "WARNING"} for name in ("weasyprint", "fontTools", "PIL")},
}
if LOG_DIR:
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
    LOGGING["handlers"]["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(Path(LOG_DIR) / "naryad.log"),
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 5,
        "encoding": "utf-8",
        "formatter": "plain",
    }
    LOGGING["root"]["handlers"].append("file")
