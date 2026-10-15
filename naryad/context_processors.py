"""Barcha shablonlar uchun: rol, ruxsatlar va menyu."""

from django.urls import reverse
from django.utils.translation import gettext as _

from . import __version__
from . import permissions as perms


def ui(request):
    user = getattr(request, "user", None)
    role = perms.user_role(user) if user is not None else None
    can = perms.permissions_for(user) if role else {}
    menu = []
    if role:
        menu.append({"label": _("Bosh sahifa"), "url": reverse("home"), "active": request.path == reverse("home")})
        if role == perms.ADMIN:
            cadets_url = reverse("cadet_list")
            weeks_url, abs_url = reverse("week_list"), reverse("absence_list")
            menu += [
                {"label": _("Haftalar"), "url": weeks_url, "active": request.path.startswith((weeks_url, "/sutka/"))},
                {"label": _("Sababli holatlar"), "url": abs_url, "active": request.path.startswith(abs_url)},
                {"label": _("Zalyotchiklar"), "url": reverse("penalty_list"), "active": request.path.startswith(reverse("penalty_list"))},
                {"label": _("Kursantlar"), "url": cadets_url, "active": request.path.startswith(cadets_url)},
                {"label": _("Statistika"), "url": reverse("stats"), "active": request.path.startswith(reverse("stats"))},
            ]
        else:
            my_url = reverse("my_card")
            on_card = user.cadet_id and request.path == reverse("cadet_detail", args=[user.cadet_id])
            # Kursant boshqa kursantlarning ro'yxatini ko'rmaydi — faqat o'z naryadi (14-bosqich, 60-band)
            menu.append({"label": _("Mening tarixim"), "url": my_url, "active": bool(on_card)})
        if can.get("admin_panel"):
            menu.append({"label": _("Boshqaruv paneli"), "url": reverse("admin:index")})
    return {
        "app_version": __version__,
        "ui_role": role,
        "ui_role_title": perms.ROLE_TITLES.get(role, ""),
        "can": can,
        "menu": menu,
    }
