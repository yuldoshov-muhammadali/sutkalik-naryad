"""Admin panel: barcha modellar, qidiruv, filtrlar va inline'lar."""

from __future__ import annotations

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import (
    Absence,
    Assignment,
    Cadet,
    ChangeLog,
    DutyDay,
    DutyWeek,
    GroupPostAssignment,
    InitialRotation,
    LoginThrottle,
    Post,
    PostSlot,
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
    fieldsets = BaseUserAdmin.fieldsets + (("Naryad platformasi", {"fields": ("role", "cadet", "must_change_password")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Naryad platformasi", {"fields": ("role", "cadet", "must_change_password")}),
    )


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

    @admin.display(description="o‘g‘il")
    def boys(self, obj):
        return obj.cadets.filter(gender="M", is_active=True).count()

    @admin.display(description="qiz")
    def girls(self, obj):
        return obj.cadets.filter(gender="F", is_active=True).count()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Cadet)
class CadetAdmin(admin.ModelAdmin):
    list_display = ("short_name", "full_name", "group", "gender", "list_number", "is_active", "duty_exempt", "duty_position")
    list_filter = ("group", "gender", "is_active", "duty_exempt")
    search_fields = ("last_name", "first_name", "patronymic", "short_name")
    # Naryaddan ozod belgisi faqat kursant kartochkasidan, sabab bilan o'zgartiriladi (jurnalga yoziladi)
    readonly_fields = ("deactivated_at", "duty_exempt", "duty_position", "created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("group", "list_number", "last_name", "first_name", "patronymic", "gender", "short_name")}),
        ("Faollik", {"fields": ("is_active", "deactivation_reason", "deactivated_at")}),
        ("Naryaddan ozod", {"fields": ("duty_exempt", "duty_position"),
                            "description": "Kursant kartochkasidagi “Naryaddan ozod qilish” / “Naryadga qaytarish” orqali o‘zgartiriladi."}),
        ("Tizim", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    actions = None

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

    @admin.display(description="o‘rinlar")
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

    @admin.display(description="sutkalar")
    def days_total(self, obj):
        return obj.days.count()

    @admin.display(description="tasdiqlangan")
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

    @admin.display(description="ogohlantirish")
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
    list_display = ("cadet", "start_date", "end_date", "reason_type", "note", "created_by")
    list_filter = ("reason_type", "cadet__group", "cadet__gender")
    date_hierarchy = "start_date"
    search_fields = ("cadet__last_name", "cadet__first_name", "note")
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


class InitialRotationFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        rows = [f.cleaned_data for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        if rows and len(rows) != 6:
            raise forms.ValidationError("Boshlang‘ich taqsimotda 6 ta joyning har biri bir martadan bo‘lishi kerak (hozir %d ta)." % len(rows))


class InitialRotationInline(admin.TabularInline):
    model = InitialRotation
    formset = InitialRotationFormSet
    fields = ("post", "group")
    extra = 6
    max_num = 6
    verbose_name_plural = (
        "Boshlang‘ich guruh → joy taqsimoti (faqat bazada tasdiqlangan tarix bo‘lmaganda, birinchi sutka uchun ishlatiladi)"
    )

    def get_extra(self, request, obj=None, **kwargs):
        return max(0, 6 - InitialRotation.objects.count())


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ("__str__", "recipient_name", "course_head_name", "course_number", "updated_at")
    readonly_fields = ("updated_by", "updated_at")
    inlines = [InitialRotationInline]

    def has_add_permission(self, request):
        return not Setting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(LoginThrottle)
class LoginThrottleAdmin(admin.ModelAdmin):
    """Bloklangan loginlar. Blokni olib tashlash — yozuvni o'chirish."""

    list_display = ("key", "failures", "last_failure_at", "blocked_until", "blocked")
    search_fields = ("key",)
    readonly_fields = ("key", "failures", "last_failure_at", "blocked_until")

    @admin.display(boolean=True, description="hozir bloklangan")
    def blocked(self, obj):
        return obj.is_blocked()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
