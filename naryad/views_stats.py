"""Statistika va adolat ko'rsatkichi sahifasi, Excel eksport (9-bosqich). Faqat admin (`history.all`)."""

from __future__ import annotations

from django.http import HttpResponse
from django.shortcuts import render

from . import permissions as perms, stats
from .models import DutyWeek, Gender, Post, SlotRole, StudyGroup

GIRL_ROLES = [SlotRole.DUTY, SlotRole.GUARD]


def cell(value: int, maximum: int, minimum: int = 0) -> dict:
    return {"value": value, "style": stats.heat(value, maximum, minimum)}


def boys_table(rows: list[stats.CadetRow], posts: list[Post]) -> list[dict]:
    max_post = max((r.by_post.get(p.code, 0) for r in rows for p in posts), default=0)
    max_role = max((r.by_role.get(x, 0) for r in rows for x in stats.ROLES), default=0)
    max_total = max((r.total for r in rows), default=0)
    min_total = min((r.total for r in rows if r.cadet.on_duty), default=0)
    return [
        {
            "row": r,
            "posts": [cell(r.by_post.get(p.code, 0), max_post) for p in posts],
            "roles": [cell(r.by_role.get(x, 0), max_role) for x in stats.ROLES],
            "total": cell(r.total, max_total, min_total),
        }
        for r in rows
    ]


def girls_table(rows: list[stats.CadetRow]) -> list[dict]:
    max_role = max((r.by_role.get(x, 0) for r in rows for x in GIRL_ROLES), default=0)
    max_total = max((r.total for r in rows), default=0)
    min_total = min((r.total for r in rows if r.cadet.on_duty), default=0)
    return [
        {"row": r, "roles": [cell(r.by_role.get(x, 0), max_role) for x in GIRL_ROLES], "total": cell(r.total, max_total, min_total)}
        for r in rows
    ]


def bar_width(value, maximum) -> int:
    return round(100 * value / maximum) if value and maximum else 0


@perms.role_required("history.all")
def stats_page(request):
    period = stats.period_from_params(request.GET)
    groups = list(StudyGroup.objects.filter(is_active=True).order_by("display_order"))
    selected = request.GET.get("guruh")
    if selected not in {g.code for g in groups}:
        selected = groups[0].code if groups else None
    posts = list(Post.objects.filter(gender=Gender.MALE).order_by("display_order"))

    rows_pool = stats.rows_by_pool(period)
    fairness = stats.fairness_all(period, rows_pool)
    by_pool = {f.pool: f for f in fairness}
    sections = stats.group_sections(period)
    max_section = max((s.by_post[p.code] for s in sections for p in posts), default=0)
    max_per_boy = max((s.per_boy or 0 for s in sections), default=0)
    manual = stats.manual_control(period)
    max_reason = max((n for _, n in manual["by_reason"]), default=0)

    context = {
        "period": period,
        "weeks": DutyWeek.objects.order_by("-start_date"),
        "groups": groups,
        "selected": selected,
        "posts": [{"code": p.code, "short": stats.POST_SHORT.get(p.code, p.name), "name": p.name} for p in posts],
        "roles": [stats.ROLE_SHORT[x] for x in stats.ROLES],
        "girl_roles": [stats.ROLE_SHORT[x] for x in GIRL_ROLES],
        "boys": boys_table(rows_pool.get(selected, []), posts) if selected else [],
        "boys_fair": by_pool.get(selected),
        "girls": girls_table(rows_pool.get(stats.GIRLS, [])),
        "girls_fair": by_pool.get(stats.GIRLS),
        "fairness": fairness,
        "sections": [
            {
                "s": s,
                "posts": [cell(s.by_post[p.code], max_section) for p in posts],
                "bar": bar_width(s.per_boy, max_per_boy),
            }
            for s in sections
        ],
        "manual": manual,
        "reason_bars": [(label, n, bar_width(n, max_reason)) for label, n in manual["by_reason"]],
        "excel_query": request.GET.urlencode(),
    }
    return render(request, "naryad/stats/index.html", context)


@perms.role_required("history.all")
def stats_excel(request):
    period = stats.period_from_params(request.GET)
    response = HttpResponse(
        stats.excel_export(period),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{stats.excel_filename(period)}"'
    return response
