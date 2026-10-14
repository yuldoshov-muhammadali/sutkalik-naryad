"""Barcha shablonlar uchun: rol, ruxsatlar va menyu."""

from django.urls import reverse

from . import permissions as perms


def ui(request):
    user = getattr(request, "user", None)
    role = perms.user_role(user) if user is not None else None
    can = perms.permissions_for(user) if role else {}
    menu = []
    if role:
        menu.append({"label": "Bosh sahifa", "url": reverse("home"), "active": request.path == reverse("home")})
        if role == perms.ADMIN:
            cadets_url = reverse("cadet_list")
            weeks_url, abs_url = reverse("week_list"), reverse("absence_list")
            menu += [
                {"label": "Haftalar", "url": weeks_url, "active": request.path.startswith((weeks_url, "/sutka/"))},
                {"label": "Sababli holatlar", "url": abs_url, "active": request.path.startswith(abs_url)},
                {"label": "Kursantlar", "url": cadets_url, "active": request.path.startswith(cadets_url)},
                {"label": "Statistika", "url": reverse("stats"), "active": request.path.startswith(reverse("stats"))},
            ]
        else:
            my_url = reverse("my_card")
            on_card = user.cadet_id and request.path == reverse("cadet_detail", args=[user.cadet_id])
            menu += [
                {"label": "Mening tarixim", "url": my_url, "active": bool(on_card)},
                {"label": "Tasdiqlangan naryadlar", "url": reverse("approved_days"),
                 "active": request.path.startswith((reverse("approved_days"), "/sutka/"))},
            ]
        if can.get("admin_panel"):
            menu.append({"label": "Boshqaruv paneli", "url": reverse("admin:index")})
    return {
        "ui_role": role,
        "ui_role_title": perms.ROLE_TITLES.get(role, ""),
        "can": can,
        "menu": menu,
    }
