"""Uch til: o'zbek (asosiy), rus, ingliz — 13-bosqich (CLAUDE.md 10-bo'lim, 59-band).

Qoidalar:
- Standart til doim o'zbekcha. Brauzer tili (Accept-Language) HISOBGA OLINMAYDI — til faqat foydalanuvchi
  tanlasa o'zgaradi: kirganlarda `User.language`, kirmaganlarda cookie.
- URL'lar o'zgarmaydi (/ru/ kabi prefiks yo'q).
- PDF naryad shakli va Excel eksport doim o'zbekcha (`translation.override("uz")`).
"""

from __future__ import annotations

import datetime as dt

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme

LANGS = ("uz", "ru", "en")
DEFAULT = "uz"

# Sana: uz — 14-oktabr 2026, ru — 14 октября 2026, en — 14 October 2026
MONTHS = {
    "uz": ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"],
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}
# Dushanbadan boshlab (date.weekday() tartibi)
WEEKDAYS = {
    "uz": ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"],
    "ru": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
}
DAY_MONTH = {"uz": "{d}-{m}", "ru": "{d} {m}", "en": "{d} {m}"}


def lang() -> str:
    code = (translation.get_language() or DEFAULT)[:2]
    return code if code in LANGS else DEFAULT


def day_month(day: dt.date) -> str:
    """14-oktabr / 14 октября / 14 October (joriy tilda)."""
    code = lang()
    return DAY_MONTH[code].format(d=day.day, m=MONTHS[code][day.month - 1])


def long_date(day: dt.date) -> str:
    """14-oktabr 2026 / 14 октября 2026 / 14 October 2026."""
    return f"{day_month(day)} {day.year}"


def weekday(day: dt.date) -> str:
    return WEEKDAYS[lang()][day.weekday()]


def weekday_inline(day: dt.date) -> str:
    """Gap ichida: “chorshanba” / “среда” / “Wednesday” (inglizchada bosh harf bilan qoladi)."""
    name = weekday(day)
    return name if lang() == "en" else name.lower()


def js_calendar() -> dict[str, str]:
    """Jonli soat uchun (static/js/app.js): JS dagi matnlar data- atributlari orqali joriy tilda beriladi.
    Hafta kunlari JS tartibida (yakshanbadan)."""
    code = lang()
    week = WEEKDAYS[code]
    return {
        "weekdays": ",".join([week[6]] + week[:6]),
        "months": ",".join(MONTHS[code]),
        "day_month": DAY_MONTH[code],
    }


# ---------------------------------------------------------------------------
# Middleware va tilni almashtirish
# ---------------------------------------------------------------------------


class LanguageMiddleware:
    """LocaleMiddleware o'rnida (SessionMiddleware dan keyin, CommonMiddleware dan oldin).

    process_request: cookie'dagi til yoki o'zbekcha (Accept-Language o'qilmaydi).
    process_view: kirgan foydalanuvchida — `User.language` ustun (boshqa qurilmada tanlagan bo'lsa ham).
    Faqat kirishdan oldin shu brauzer sessiyasida tugma bilan aniq tanlangan til undan ustun va saqlanadi.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, DEFAULT)
        if code not in LANGS:
            code = DEFAULT
        translation.activate(code)
        request.LANGUAGE_CODE = code
        response = self.get_response(request)
        wanted = getattr(request, "_language_cookie", None)
        if wanted:
            set_cookie(response, wanted)
        response.headers.setdefault("Content-Language", translation.get_language())
        translation.deactivate()
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            code = getattr(user, "language", "")
            chosen = request.session.pop(CHOSEN_KEY, None) if hasattr(request, "session") else None
            if chosen in LANGS and chosen != code:
                # kirish sahifasida hozirgina tanlangan til — foydalanuvchiga saqlanadi
                get_user_model().objects.filter(pk=user.pk).update(language=chosen)
                user.language = code = chosen
            if not code:
                # hali tanlamagan — kirish sahifasida (cookie'da) tanlagani saqlanadi
                if request.LANGUAGE_CODE != DEFAULT or settings.LANGUAGE_COOKIE_NAME in request.COOKIES:
                    get_user_model().objects.filter(pk=user.pk).update(language=request.LANGUAGE_CODE)
                    user.language = request.LANGUAGE_CODE
                return
            if code in LANGS and code != request.LANGUAGE_CODE:
                translation.activate(code)
                request.LANGUAGE_CODE = code
                request._language_cookie = code  # shu qurilmada ham cookie yangilansin
        return


# kirmagan foydalanuvchi tugma bilan tanlagan til (kirgach User.language ga o'tadi)
CHOSEN_KEY = "naryad_til_tanlandi"


def set_cookie(response, code: str) -> None:
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        code,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )


def set_language(request):
    """POST (CSRF bilan): til tanlovi. Kirgan bo'lsa — User.language ga ham yoziladi. O'sha sahifaga qaytadi."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    code = request.POST.get("language", "")
    nxt = request.POST.get("next") or "/"
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        nxt = "/"
    response = HttpResponseRedirect(nxt)
    if code in LANGS:
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            if user.language != code:
                user.language = code
                user.save(update_fields=["language"])
        elif hasattr(request, "session"):
            request.session[CHOSEN_KEY] = code
        set_cookie(response, code)
        request._language_cookie = None
    return response
