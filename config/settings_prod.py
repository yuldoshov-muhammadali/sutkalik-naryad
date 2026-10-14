"""Production (server) sozlamalari: DJANGO_SETTINGS_MODULE=config.settings_prod.

Asosiy sozlamalar config/settings.py da; bu yerda faqat xavfsizlik qat'iylashtiriladi.
`python manage.py check --deploy` ogohlantirishsiz o'tishi kerak (docs/xavfsizlik.md).

DJANGO_HTTPS=False — faqat internetsiz ichki tarmoq varianti uchun (docs/joylashtirish.md, B variant):
HTTPS'ga majburlash, xavfsiz cookie va HSTS o'chadi (check --deploy buni ogohlantiradi — bu kutilgan).
"""

import os

from django.core.exceptions import ImproperlyConfigured

os.environ["DJANGO_DEBUG"] = "False"

from .settings import *  # noqa: E402,F403
from .settings import env_bool, env_list  # noqa: E402

DEBUG = False

if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5:  # noqa: F405
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY kamida 50 belgidan iborat tasodifiy qiymat bo‘lishi kerak: "
        "python -c \"import secrets; print(secrets.token_urlsafe(50))\""
    )
if not env_list("DJANGO_ALLOWED_HOSTS"):
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS berilmagan (masalan: naryad.example.uz).")

HTTPS = env_bool("DJANGO_HTTPS", default=True)

if HTTPS:
    # Caddy (yoki Railway) HTTPS'ni tugatadi va X-Forwarded-Proto yuboradi
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", str(365 * 24 * 60 * 60)))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_SUBDOMAINS", default=True)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", default=True)
    SESSION_COOKIE_NAME = "__Secure-sessionid"
    CSRF_COOKIE_NAME = "__Secure-csrftoken"

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
