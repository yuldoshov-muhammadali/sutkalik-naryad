"""Kirish: login urinishlarini cheklash va birinchi kirishda parolni majburiy almashtirish."""

from __future__ import annotations

import datetime as dt

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import ngettext

from .models import LoginThrottle


def max_failures() -> int:
    return getattr(settings, "LOGIN_MAX_FAILURES", 5)


def block_minutes() -> int:
    return getattr(settings, "LOGIN_BLOCK_MINUTES", 15)


def throttle_key(username: str) -> str:
    return (username or "").strip().casefold()[:150]


def blocked_message(throttle: LoginThrottle) -> str:
    left = max(1, int((throttle.blocked_until - timezone.now()).total_seconds() // 60) + 1)
    return ngettext(
        "Juda ko‘p noto‘g‘ri urinish (%(failures)s marta). Bu login %(minutes)s daqiqaga bloklandi — "
        "taxminan %(left)s daqiqadan keyin qayta urinib ko‘ring.",
        "Juda ko‘p noto‘g‘ri urinish (%(failures)s marta). Bu login %(minutes)s daqiqaga bloklandi — "
        "taxminan %(left)s daqiqadan keyin qayta urinib ko‘ring.",
        left,
    ) % {"failures": max_failures(), "minutes": block_minutes(), "left": left}


@transaction.atomic
def register_failure(username: str) -> LoginThrottle:
    now = timezone.now()
    throttle, _ = LoginThrottle.objects.select_for_update().get_or_create(key=throttle_key(username))
    window = dt.timedelta(minutes=block_minutes())
    if throttle.last_failure_at is None or now - throttle.last_failure_at > window or (
        throttle.blocked_until and throttle.blocked_until <= now
    ):
        throttle.failures = 0
        throttle.blocked_until = None
    throttle.failures += 1
    throttle.last_failure_at = now
    if throttle.failures >= max_failures():
        throttle.blocked_until = now + window
    throttle.save()
    return throttle


def reset_failures(username: str) -> None:
    LoginThrottle.objects.filter(key=throttle_key(username)).delete()


class ThrottleMixin:
    """AuthenticationForm uchun: blokni tekshiradi, xatolarni sanaydi."""

    def clean(self):
        username = self.data.get("username", "")
        throttle = LoginThrottle.objects.filter(key=throttle_key(username)).first()
        if throttle and throttle.is_blocked():
            raise forms.ValidationError(blocked_message(throttle), code="blocked")
        try:
            cleaned = super().clean()
        except forms.ValidationError:
            throttle = register_failure(username)
            if throttle.is_blocked():
                raise forms.ValidationError(blocked_message(throttle), code="blocked") from None
            raise
        reset_failures(username)
        return cleaned


class LoginForm(ThrottleMixin, AuthenticationForm):
    error_messages = {
        "invalid_login": _lazy("Login yoki parol noto‘g‘ri. Ikkalasida ham katta-kichik harf farqlanadi."),
        "inactive": _lazy("Bu akkaunt faol emas."),
    }

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = _lazy("Login")
        self.fields["username"].widget.attrs.update({"autocapitalize": "none", "autocomplete": "username"})
        self.fields["password"].label = _lazy("Parol")


class AdminLoginForm(ThrottleMixin, AdminAuthenticationForm):
    error_messages = {
        **AdminAuthenticationForm.error_messages,
        "invalid_login": _lazy("Login yoki parol noto‘g‘ri yoki boshqaruv paneliga kirish huquqi yo‘q."),
    }


class ForcePasswordChangeMiddleware:
    """`must_change_password` belgilangan foydalanuvchini parol sahifasiga yo'naltiradi."""

    ALLOWED_PREFIXES = ("/static/",)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and getattr(user, "must_change_password", False):
            allowed = {reverse("password_change"), reverse("logout"), reverse("set_language")}
            if request.path not in allowed and not request.path.startswith(self.ALLOWED_PREFIXES):
                messages.warning(request, _lazy("Xavfsizlik uchun avval vaqtinchalik parolni o‘zingizning parolingizga almashtiring."))
                return redirect("password_change")
        return self.get_response(request)
