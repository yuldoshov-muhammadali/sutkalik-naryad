"""Barcha shablonlar uchun: rol, ruxsatlar va menyu."""

from django.conf import settings
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
        if perms.is_staff_role(role):
            cadets_url = reverse("cadet_list")
            weeks_url, abs_url = reverse("week_list"), reverse("absence_list")
            menu += [
                {"label": _("Haftalar"), "url": weeks_url, "active": request.path.startswith((weeks_url, "/sutka/"))},
                {"label": _("Sababli holatlar"), "url": abs_url, "active": request.path.startswith(abs_url)},
                {"label": _("Kasallar ro‘yxati"), "url": reverse("sick_list"), "active": request.path.startswith(reverse("sick_list"))},
                {"label": _("Zalyotchiklar"), "url": reverse("penalty_list"), "active": request.path.startswith(reverse("penalty_list"))},
                {"label": _("Kursantlar"), "url": cadets_url, "active": request.path.startswith(cadets_url)},
                {"label": _("Statistika"), "url": reverse("stats"), "active": request.path.startswith(reverse("stats"))},
            ]
        else:
            my_url = reverse("my_card")
            on_card = user.cadet_id and request.path == reverse("cadet_detail", args=[user.cadet_id])
            # 16-bosqich: “Tasdiqlangan naryadlar” qaytdi (faqat tasdiqlangan sutkalar, o'qish uchun)
            menu += [
                {"label": _("Mening tarixim"), "url": my_url, "active": bool(on_card)},
            ]
            if role == perms.COMMANDER:  # 19-bosqich: faqat o'z guruhi, faqat ko'rish
                gp = reverse("group_penalties")
                menu.append({"label": _("Mening guruhim"), "url": reverse("group_overview"),
                             "active": request.path.startswith(reverse("group_overview")) and not request.path.startswith((gp, reverse("group_penalty_add")))})
                menu.append({"label": _("Guruh zalyotlari"), "url": gp,  # 20-bosqich
                             "active": request.path.startswith((gp, reverse("group_penalty_add")))})
            menu += [
                {"label": _("Tasdiqlangan naryadlar"), "url": reverse("approved_days"),
                 "active": request.path.startswith((reverse("approved_days"), "/sutka/"))},
            ]
        if can.get("admin_panel"):
            menu.append({"label": _("Boshqaruv paneli"), "url": reverse("admin:index")})
    return {
        "app_version": __version__,
        "platform_name": settings.SITE_NAME,  # "site_name" emas — Django login sahifasi o'zinikini qo'yadi
        "ui_role": role,
        "ui_role_title": perms.ROLE_TITLES.get(role, ""),
        "can": can,
        "menu": menu,
    }
