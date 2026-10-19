"""“Sinov ma'lumotlarini tozalash” sahifasi (20-bosqich, CLAUDE.md 69-band) — faqat admin."""

from __future__ import annotations

import re

from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from . import cleanup
from . import permissions as perms

BACKUP_NAME = re.compile(r"^zaxira_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.json\.gz$")


def _backups():
    directory = cleanup.backup_dir()
    if not directory.exists():
        return []
    return sorted((p for p in directory.iterdir() if BACKUP_NAME.match(p.name)), reverse=True)[:10]


@perms.role_required("settings.manage")
def clear_preview(request):
    """Ko'rib chiqish — hech narsa o'chirilmaydi."""
    return render(request, "naryad/settings/clear.html", {
        "p": cleanup.preview(), "word_1": cleanup.WORD_1, "word_2": cleanup.WORD_2, "backups": _backups(),
        "step": request.GET.get("bosqich", ""),
    })


@require_POST
@perms.role_required("settings.manage")
def clear_run(request):
    try:
        result = cleanup.clear(request.user, request.POST.get("word_1", ""), request.POST.get("word_2", ""), request.POST.get("token", ""))
    except cleanup.CleanupError as exc:
        messages.error(request, str(exc))
        return redirect("clear_test_data")
    messages.success(request, _("Sinov ma’lumotlari tozalandi. Zaxira: %(name)s — darhol yuklab oling.") % {"name": result.backup.name})
    return redirect("clear_test_data")


@perms.role_required("settings.manage")
def backup_download(request, name):
    if not BACKUP_NAME.match(name):
        raise Http404
    path = cleanup.backup_dir() / name
    if not path.is_file():
        raise Http404
    response = FileResponse(path.open("rb"), as_attachment=True, filename=name, content_type="application/gzip")
    response["Cache-Control"] = "private, no-store"
    return response
