"""Admin panel: barcha modellar, qidiruv, filtrlar va inline'lar."""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db import models
from django.http import HttpResponse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import ngettext, pgettext_lazy

from naryad.engine import config as engine_config

from .models import (
    POSITION_LABELS,
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    GroupPostAssignment,
    InitialRotation,
    LoginThrottle,
    Penalty,
    Post,
    PostSlot,
    PrepNote,
    Setting,
    StudyGroup,
    User,
)

# Django'ning "Guruhlar (huquqlar)" bo'limi ishlatilmaydi: rollar User.role da (docs/05-rollar.md)
if admin.site.is_registered(Group):
    admin.site.unregister(Group)

# ---------------------------------------------------------------------------
# Foydalanuvchilar
# ---------------------------------------------------------------------------


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "first_name", "last_name", "role", "cadet", "must_change_password", "is_active", "last_login")
    list_filter = ("role", "must_change_password", "is_active", "is_superuser")
    search_fields = ("username", "first_name", "last_name", "cadet__last_name", "cadet__first_name")
    autocomplete_fields = ("cadet",)
    fieldsets = BaseUserAdmin.fieldsets + ((_lazy("Naryad platformasi"), {"fields": ("role", "cadet", "must_change_password")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (_lazy("Naryad platformasi"), {
            "fields": ("role", "cadet", "must_change_password"),
            "description": _lazy("“Guruh komandiri” roli faqat guruh komandiri lavozimidagi kursantga beriladi; guruh kursantning guruhidan olinadi, har guruhga bitta faol komandir. “Kadir” roli — admin bilan bir xil amallar, lekin boshqaruv paneli va Sozlamalarsiz (kursantga bog‘lash shart emas)."),
        }),
    )
    actions = ["reset_temp_passwords"]

    @admin.action(description=_lazy("Vaqtinchalik parol berish (Excel)"))
    def reset_temp_passwords(self, request, queryset):
        """Parolni tiklash (kursant va komandir): yangi vaqtinchalik parol, birinchi kirishda almashtirish majburiy."""
        from .accounts import accounts_xlsx_bytes, reset_passwords

        accounts = reset_passwords(queryset.exclude(role="admin").filter(is_superuser=False))
        if not accounts:
            self.message_user(request, _lazy("Kursantga bog‘langan akkaunt tanlanmadi."), level="warning")
            return None
        return _xlsx_response(accounts_xlsx_bytes(accounts, timezone.localdate()), "parollar")


# ---------------------------------------------------------------------------
# Guruhlar va kursantlar
# ---------------------------------------------------------------------------


class CadetInline(admin.TabularInline):
    model = Cadet
    fields = ("list_number", "last_name", "first_name", "patronymic", "gender", "short_name", "is_active")
    extra = 0
    show_change_link = True
    can_delete = False


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ("code", "direction", "language", "display_order", "is_active", "boys", "girls")
    list_filter = ("is_active", "language")
    search_fields = ("code", "direction")
    inlines = [CadetInline]

    @admin.display(description=_lazy("o‘g‘il"))
    def boys(self, obj):
        return obj.cadets.filter(gender="M", is_active=True).count()

    @admin.display(description=_lazy("qiz"))
    def girls(self, obj):
        return obj.cadets.filter(gender="F", is_active=True).count()

    def has_delete_permission(self, request, obj=None):
        return False


def _xlsx_response(content: bytes, prefix: str) -> HttpResponse:
    response = HttpResponse(content, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = f'attachment; filename="{prefix}_{timezone.localdate():%Y-%m-%d}.xlsx"'
    response["Cache-Control"] = "private, no-store"  # ochiq parollar
    return response


class PositionFilter(admin.SimpleListFilter):
    """“Lavozim” filtri (21-bosqich, 5a): Hammasi / Guruh komandiri / Kurs starshinasi / Kurs pisari / Kaptyorchik / Lavozimsiz."""

    title = pgettext_lazy("kursant lavozimi", "Lavozim")
    parameter_name = "lavozim"

    def lookups(self, request, model_admin):
        return [*POSITION_LABELS.items(), ("yoq", _lazy("Lavozimsiz"))]

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yoq":
            return queryset.filter(duty_exempt=False)
        if value == "komandir":
            return queryset.filter(duty_exempt=True, duty_position__iendswith="guruh komandiri")
        if value in POSITION_LABELS:
            return queryset.filter(duty_exempt=True, duty_position__icontains=value)
        return queryset


@admin.register(Cadet)
class CadetAdmin(admin.ModelAdmin):
    list_display = ("short_name", "fio", "group", "gender", "list_number", "is_active", "position")
    list_filter = ("group", "gender", "is_active", PositionFilter)
    search_fields = ("last_name", "first_name", "patronymic", "short_name")
    # Lavozim belgisi faqat kursant kartochkasidan, sabab bilan o'zgartiriladi (jurnalga yoziladi)
    readonly_fields = ("deactivated_at", "duty_exempt", "duty_position", "created_at", "updated_at")
    actions = ["create_accounts"]

    @admin.action(description=_lazy("Akkaunt yaratish (Excel) — guruh komandirlariga rol avtomatik"))
    def create_accounts(self, request, queryset):
        from .accounts import accounts_xlsx_bytes, create_cadet_accounts

        report = create_cadet_accounts(None, cadets=queryset)
        if not report.created:
            self.message_user(request, _lazy("Yangi akkaunt yaratilmadi: tanlanganlarning akkaunti bor yoki faol emas."), level="warning")
            return None
        return _xlsx_response(accounts_xlsx_bytes(report.created, timezone.localdate()), "akkauntlar")
    fieldsets = (
        (None, {"fields": ("group", "list_number", "last_name", "first_name", "patronymic", "gender", "short_name")}),
        (_lazy("Faollik"), {"fields": ("is_active", "deactivation_reason", "deactivated_at")}),
        (pgettext_lazy("kursant lavozimi", "Lavozim"), {"fields": ("duty_exempt", "duty_position"),
                            "description": _lazy("Kursant kartochkasidagi “Lavozim belgilash” / “Lavozimni olib tashlash” orqali o‘zgartiriladi.")}),
        (_lazy("Tizim"), {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description=_lazy("F.I.Sh."))
    def fio(self, obj):
        return obj.full_name

    @admin.display(description=pgettext_lazy("kursant lavozimi", "Lavozim"))
    def position(self, obj):
        return obj.position_label or "—"

    def has_delete_permission(self, request, obj=None):
        # Kursant o'chirilmaydi — faqat faolsizlantiriladi (tarix saqlanadi)
        return False


# ---------------------------------------------------------------------------
# Joylar (qulflangan: faqat ko'rish)
# ---------------------------------------------------------------------------


class ReadOnlyAdminMixin:
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class PostSlotInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = PostSlot
    fields = ("position", "role", "print_label", "show_label")
    readonly_fields = fields
    extra = 0


@admin.register(Post)
class PostAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("display_order", "name", "gender", "rotation_index", "size")
    list_display_links = ("name",)
    list_filter = ("gender",)
    inlines = [PostSlotInline]

    @admin.display(description=_lazy("o‘rinlar"))
    def size(self, obj):
        return obj.slots.count()


@admin.register(PostSlot)
class PostSlotAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("post", "position", "role", "print_label", "show_label")
    list_filter = ("post", "role")


# ---------------------------------------------------------------------------
# Hafta va sutka
# ---------------------------------------------------------------------------


class DutyDayInline(admin.TabularInline):
    model = DutyDay
    fields = ("date", "status", "generated_at", "approved_at")
    readonly_fields = fields
    extra = 0
    show_change_link = True
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(DutyWeek)
class DutyWeekAdmin(admin.ModelAdmin):
    list_display = ("__str__", "start_date", "days_total", "days_approved", "created_by", "created_at")
    date_hierarchy = "start_date"
    search_fields = ("note",)
    readonly_fields = ("created_by", "created_at")
    inlines = [DutyDayInline]

    @admin.display(description=_lazy("sutkalar"))
    def days_total(self, obj):
        return obj.days.count()

    @admin.display(description=_lazy("tasdiqlangan"))
    def days_approved(self, obj):
        return obj.days.filter(status=DutyDay.Status.APPROVED).count()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # 2-kurs haftasini faqat admin (kurs boshlig'i) ochadi — CLAUDE.md 10-bo'lim, 14-band
    def has_add_permission(self, request):
        return getattr(request.user, "is_admin_role", False) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return getattr(request.user, "is_admin_role", False) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if not getattr(request.user, "is_admin_role", False):
            return False
        return obj is None or not obj.days.exists()


class GroupPostAssignmentInline(admin.TabularInline):
    model = GroupPostAssignment
    fields = ("post", "group")
    extra = 0


class AssignmentInline(admin.TabularInline):
    model = Assignment
    fields = ("post_slot", "cadet", "group", "source", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("cadet",)
    extra = 0


class ChangeLogInline(ReadOnlyAdminMixin, admin.TabularInline):
    model = ChangeLog
    fields = ("created_at", "action", "post_slot", "old_cadet", "new_cadet", "reason", "user")
    readonly_fields = fields
    extra = 0


@admin.register(DutyDay)
class DutyDayAdmin(admin.ModelAdmin):
    list_display = ("__str__", "date", "week", "status", "warnings_count", "generated_by", "approved_by", "approved_at")
    list_filter = ("status", "week")
    date_hierarchy = "date"
    search_fields = ("assignments__cadet__last_name", "assignments__cadet__first_name")
    readonly_fields = ("warnings", "generated_by", "generated_at", "approved_by", "approved_at")
    inlines = [GroupPostAssignmentInline, AssignmentInline, ChangeLogInline]

    @admin.display(description=_lazy("ogohlantirish"))
    def warnings_count(self, obj):
        return len(obj.warnings or [])

    def has_delete_permission(self, request, obj=None):
        # Tasdiqlangan sutka va jurnali bor sutka o'chirilmaydi
        return obj is not None and not obj.is_approved and not obj.changes.exists()


@admin.register(GroupPostAssignment)
class GroupPostAssignmentAdmin(admin.ModelAdmin):
    list_display = ("duty_day", "post", "group")
    list_filter = ("post", "group", "duty_day__status")
    date_hierarchy = "duty_day__date"


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("duty_day", "post_slot", "cadet", "group", "source")
    list_filter = ("duty_day__status", "post_slot__post", "group", "source", "cadet__gender")
    date_hierarchy = "duty_day__date"
    search_fields = ("cadet__last_name", "cadet__first_name", "cadet__short_name")
    autocomplete_fields = ("cadet",)
    list_select_related = ("duty_day", "post_slot__post", "cadet__group", "group")


# ---------------------------------------------------------------------------
# Sababli yo'qlik, jurnal, sozlamalar
# ---------------------------------------------------------------------------


@admin.register(Absence)
class AbsenceAdmin(admin.ModelAdmin):
    list_display = ("cadet", "start_date", "end_date", "reason_type", "illness", "note", "created_by")
    list_filter = ("reason_type", "cadet__group", "cadet__gender")
    date_hierarchy = "start_date"
    search_fields = ("cadet__last_name", "cadet__first_name", "note", "illness")
    autocomplete_fields = ("cadet",)
    readonly_fields = ("created_by", "created_at")

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ChangeLog)
class ChangeLogAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("created_at", "duty_day", "action", "post_slot", "old_cadet", "new_cadet", "user", "reason")
    list_filter = ("action", "duty_day__status")
    date_hierarchy = "created_at"
    search_fields = ("reason", "old_cadet__last_name", "new_cadet__last_name", "user__username")


@admin.register(Penalty)
class PenaltyAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Faqat ko'rish: zalyot “Zalyotchiklar” sahifasida kiritiladi/bekor qilinadi (jurnalga yoziladi)."""

    list_display = ("cadet", "reason_type", "order_date", "count", "status", "created_by", "created_at")
    list_filter = ("status", "reason_type")
    search_fields = ("cadet__last_name", "cadet__first_name", "note", "illness")


class InitialRotationFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        rows = [f.cleaned_data for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if rows and len(rows) != 6:
            raise forms.ValidationError(
                ngettext(
                    "Boshlang‘ich taqsimotda 6 ta joyning har biri bir martadan bo‘lishi kerak (hozir %(n)d ta).",
                    "Boshlang‘ich taqsimotda 6 ta joyning har biri bir martadan bo‘lishi kerak (hozir %(n)d ta).",
                    len(rows),
                )
                % {"n": len(rows)}
            )


class InitialRotationInline(admin.TabularInline):
    model = InitialRotation
    formset = InitialRotationFormSet
    fields = ("post", "group")
    extra = 6
    max_num = 6
    verbose_name_plural = (
        _lazy("Boshlang‘ich guruh → joy taqsimoti (faqat bazada tasdiqlangan tarix bo‘lmaganda, birinchi sutka uchun ishlatiladi)")
    )

    def get_extra(self, request, obj=None, **kwargs):
        return max(0, 6 - InitialRotation.objects.count())


class PrepNoteInline(admin.StackedInline):
    """Har joy uchun tayyorgarlik eslatmasi, uch tilda (14-bosqich). Bo'sh bo'lsa kursantga ko'rsatilmaydi."""

    model = PrepNote
    fields = ("post", "text_uz", "text_ru", "text_en")
    readonly_fields = ("post",)
    extra = 0
    can_delete = False
    # Har joy alohida blokda, uch til ostma-ost (jadval ko'rinishida 1280 px’dan kengayib ketadi)
    formfield_overrides = {models.CharField: {"widget": forms.TextInput(attrs={"size": 80})}}

    def has_add_permission(self, request, obj=None):
        return False


class SettingForm(forms.ModelForm):
    """Og'ir joylar — o'g'il bolalar joylaridan belgilanadi (Qizlar yotoqxonasi kirmaydi)."""

    hard_posts = forms.MultipleChoiceField(
        label=_lazy("og‘ir joylar"), required=False, widget=forms.CheckboxSelectMultiple,
        help_text=_lazy("Bir haftada kursant ko‘pi bilan bittasida turadi. Qizlar yotoqxonasi kirmaydi."),
    )

    class Meta:
        model = Setting
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["hard_posts"].choices = [
            (code, _lazy(engine_config.POSTS_BY_CODE[code].name)) for code in engine_config.ROTATION_CHAIN
        ]


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    form = SettingForm
    list_display = ("__str__", "recipient_name", "course_head_name", "course_number", "approval_lead_hours", "updated_at")
    readonly_fields = ("updated_by", "updated_at", "test_data_link")
    inlines = [InitialRotationInline, PrepNoteInline]
    fieldsets = (
        (None, {"fields": (
            "recipient_position", "recipient_name", "course_head_position", "course_head_rank", "course_head_name",
            "course_number", "approval_lead_hours", "penalty_per_post",
            "commander_penalty_max", "commander_order_max_age_days", "commander_daily_limit",
        )}),
        (_lazy("Joylar navbati va og‘ir joylar (21-bosqich)"), {
            "fields": ("post_rotation_enabled", "hard_posts"),
            "description": _lazy(
                "Haftada (yakshanba 18:00 – yakshanba 18:00) kursant ko‘pi bilan bitta og‘ir joyda turadi; oxirgi marta "
                "turgan joyiga qayta qo‘yilmaydi; 5 ta katta joyning hammasida turmaguncha bittasi takrorlanmaydi. "
                "Kecha naryadda bo‘lgan kursantni generator hech qachon qo‘ymaydi. O‘chiq bo‘lsa — avvalgi tartib."
            ),
        }),
        (_lazy("Tizim"), {"fields": ("updated_by", "updated_at", "test_data_link")}),
    )

    @admin.display(description=_lazy("Sinov ma’lumotlarini tozalash"))
    def test_data_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html

        return format_html('<a href="{}">{}</a>', reverse("clear_test_data"), _lazy("Ko‘rib chiqish va tozalash →"))

    def change_view(self, request, object_id, form_url="", extra_context=None):
        # Har bir joy uchun eslatma qatori bo'lsin (yangi joy qo'shilsa ham)
        if Setting.objects.filter(pk=object_id).exists():
            for post in Post.objects.filter(prep_note__isnull=True):
                PrepNote.objects.get_or_create(post=post, defaults={"setting_id": int(object_id)})
        return super().change_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request):
        return not Setting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        if change and {"post_rotation_enabled", "hard_posts"} & set(form.changed_data):
            # 21-bosqich: yoqish/o'chirish jurnalga yoziladi; faqat keyingi tuziladigan sutkalarga ta'sir qiladi
            state = "yoqildi" if obj.post_rotation_enabled else "o‘chirildi"
            names = ", ".join(engine_config.POSTS_BY_CODE[c].name for c in obj.hard_posts if c in engine_config.POSTS_BY_CODE)
            ChangeLog.objects.create(
                action=ChangeLog.Action.POST_ROTATION, user=request.user,
                details=f"Joylar navbati va og‘ir joylar: {state}. Og‘ir joylar: {names or '—'}.",
            )


@admin.register(LoginThrottle)
class LoginThrottleAdmin(admin.ModelAdmin):
    """Bloklangan loginlar. Blokni olib tashlash — yozuvni o'chirish."""

    list_display = ("key", "failures", "last_failure_at", "blocked_until", "blocked")
    search_fields = ("key",)
    readonly_fields = ("key", "failures", "last_failure_at", "blocked_until")

    @admin.display(boolean=True, description=_lazy("hozir bloklangan"))
    def blocked(self, obj):
        return obj.is_blocked()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
