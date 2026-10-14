"""Xavfsizlik va ishga tushirish uchun middleware'lar (10-bosqich).

- HealthCheckMiddleware: /health/ — konteyner healthcheck'i uchun. Eng birinchi middleware:
  Host sarlavhasi (ALLOWED_HOSTS) va HTTPS yo'naltirishidan oldin ishlaydi, shuning uchun
  konteyner ichidan http://127.0.0.1:8000/health/ bilan tekshirish mumkin. Faqat "ok"/"xato" qaytaradi.
- ContentSecurityPolicyMiddleware: HTML javoblarga Content-Security-Policy sarlavhasi.
  Skriptlar faqat o'z serverimizdan (inline JavaScript yo'q); inline style ruxsat
  (issiqlik xaritasi ranglari va HTMX indikatori uchun).
"""

from __future__ import annotations

import logging

from django.conf import settings
from django.db import connection
from django.http import JsonResponse

logger = logging.getLogger("naryad")

HEALTH_PATH = "/health/"

DEFAULT_CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data:",
        "font-src 'self'",
        "connect-src 'self'",
        "frame-src 'self'",
        "frame-ancestors 'none'",
        "form-action 'self'",
        "base-uri 'self'",
        "object-src 'none'",
    ]
)


class HealthCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == HEALTH_PATH and request.method in ("GET", "HEAD"):
            return health_response()
        return self.get_response(request)


def health_response() -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # noqa: BLE001 — baza ishlamasa ham javob qaytadi
        logger.exception("Health check: bazaga ulanib bo'lmadi")
        return JsonResponse({"status": "xato", "database": "xato"}, status=503)
    return JsonResponse({"status": "ok", "database": "ok"})


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.policy = getattr(settings, "CONTENT_SECURITY_POLICY", DEFAULT_CSP)

    def __call__(self, request):
        response = self.get_response(request)
        if self.policy and response.get("Content-Type", "").startswith("text/html"):
            response.setdefault("Content-Security-Policy", self.policy)
        return response
