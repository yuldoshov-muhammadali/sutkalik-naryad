"""Sutkalik naryad platformasi modellari (docs/01-talablar-va-sxema.md, 4-bo'lim).

Vaqt: bazada faqat sanalar saqlanadi. Sutka shu sanada 18:00 da boshlanadi,
2-kurs haftasi yakshanba 18:00 dan keyingi yakshanba 18:00 gacha (7 sutka).
Statistika saqlanmaydi — tasdiqlangan sutkalardagi Assignment dan hisoblanadi.
"""

from __future__ import annotations

import datetime as dt

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from naryad.engine import config as engine_config
from naryad.engine import models as em
from naryad.engine.allocator import week_start as engine_week_start
from naryad.engine.names import normalize_apostrophes, short_name as make_short_name


class Gender(models.TextChoices):
    MALE = em.MALE, "O‘g‘il"
    FEMALE = em.FEMALE, "Qiz"


class SlotRole(models.TextChoices):
    DUTY = em.ROLE_DUTY, "Navbatchi"
    ASSISTANT = em.ROLE_ASSISTANT, "Navbatchi yordamchisi"
    GUARD = em.ROLE_GUARD, "Posbon"


def duty_start(day: dt.date) -> dt.datetime:
    """Sutka boshlanish vaqti (Asia/Tashkent, 18:00) — timezone-aware."""
    naive = dt.datetime.combine(day, engine_config.DUTY_START_TIME)
    return timezone.make_aware(naive, timezone.get_default_timezone())


# ---------------------------------------------------------------------------
# Foydalanuvchi
# ---------------------------------------------------------------------------


class UserRole(models.TextChoices):
    ADMIN = "admin", "Admin (kurs boshlig‘i)"
    CADET = "cadet", "Kursant (faqat ko‘rish)"


class AppUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Tizim foydalanuvchisi: rol va (ixtiyoriy) bog'langan kursant."""

    role = models.CharField("rol", max_length=10, choices=UserRole.choices, default=UserRole.CADET)
    cadet = models.OneToOneField(
        "Cadet",
        verbose_name="kursant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="user",
    )

    must_change_password = models.BooleanField(
        "parolni almashtirishi shart",
        default=False,
        help_text="Belgilansa, foydalanuvchi keyingi kirishda parolini almashtirmaguncha boshqa sahifalarga o‘ta olmaydi.",
    )

    objects = AppUserManager()

    class Meta:
        db_table = "app_user"
        verbose_name = "foydalanuvchi"
        verbose_name_plural = "foydalanuvchilar"
        constraints = [
            models.CheckConstraint(condition=Q(role__in=UserRole.values), name="app_user_role_valid"),
        ]

    def clean(self):
        super().clean()
        if self.role == UserRole.CADET and not self.cadet_id and not self.is_superuser:
            raise ValidationError({"cadet": "Kursant roli uchun kursant tanlanishi shart."})

    def save(self, *args, **kwargs):
        # Admin panelga faqat admin roli va superuser kiradi (CLAUDE.md 10-bo'lim, 19-band)
        self.is_staff = self.is_superuser or self.role == UserRole.ADMIN
        super().save(*args, **kwargs)

    def has_perm(self, perm, obj=None):
        # Admin (kurs boshlig'i) — hammasi (CLAUDE.md 6-bo'lim)
        if self.is_active and self.role == UserRole.ADMIN:
            return True
        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        if self.is_active and self.role == UserRole.ADMIN:
            return True
        return super().has_module_perms(app_label)

    @property
    def is_admin_role(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_superuser


# ---------------------------------------------------------------------------
# Guruh va kursant
# ---------------------------------------------------------------------------


class StudyGroup(models.Model):
    """O'quv guruhi (CLAUDE.md: group). Rotatsiya va adolat hisobi shu kesimda."""

    class Language(models.TextChoices):
        UZ = "uz", "O‘zbek"
        RU = "ru", "Rus"

    code = models.CharField("guruh kodi", max_length=20, unique=True, help_text="Masalan: BI-525")
    direction = models.CharField("ta’lim yo‘nalishi", max_length=100)
    language = models.CharField("ta’lim tili", max_length=2, choices=Language.choices, default=Language.UZ)
    display_order = models.PositiveSmallIntegerField("tartib raqami", unique=True)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        db_table = "study_group"
        ordering = ["display_order"]
        verbose_name = "guruh"
        verbose_name_plural = "guruhlar"

    def __str__(self) -> str:
        return self.code


class Cadet(models.Model):
    """Kursant. O'chirilmaydi — faqat faolsizlantiriladi (tarix saqlanadi)."""

    group = models.ForeignKey(StudyGroup, verbose_name="guruh", on_delete=models.PROTECT, related_name="cadets")
    last_name = models.CharField("familiya", max_length=60)
    first_name = models.CharField("ism", max_length=60)
    patronymic = models.CharField("otasining ismi", max_length=100, blank=True)
    gender = models.CharField("jinsi", max_length=1, choices=Gender.choices)
    list_number = models.PositiveSmallIntegerField("ro‘yxatdagi raqami", null=True, blank=True)
    short_name = models.CharField(
        "qisqa ism (PDF)",
        max_length=60,
        blank=True,
        help_text="Bo‘sh qoldirilsa avtomatik: Familiya + ism bosh harfi (Shavkatov Sh, G‘ayratov G‘).",
    )
    is_active = models.BooleanField("faol", default=True)
    deactivated_at = models.DateTimeField("faolsizlantirilgan vaqti", null=True, blank=True)
    deactivation_reason = models.CharField("faolsizlantirish sababi", max_length=200, blank=True)
    # Komandirlar va kurs lavozimlari: faol (akkaunti ishlaydi), lekin sutkalik naryadga qo'yilmaydi
    # (CLAUDE.md 2- va 4-bo'lim, 10-bo'lim 56-band). Faqat kursant kartochkasidan, sabab bilan o'zgartiriladi.
    duty_exempt = models.BooleanField("naryaddan ozod", default=False)
    duty_position = models.CharField(
        "lavozimi", max_length=100, blank=True, help_text="Masalan: Kurs starshinasi, BI-225 guruh komandiri."
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)
    updated_at = models.DateTimeField("o‘zgartirilgan", auto_now=True)

    class Meta:
        db_table = "cadet"
        ordering = ["group__display_order", "list_number", "last_name", "first_name"]
        verbose_name = "kursant"
        verbose_name_plural = "kursantlar"
        constraints = [
            models.UniqueConstraint(
                fields=["group", "last_name", "first_name", "patronymic"], name="cadet_unique_name_in_group"
            ),
            models.UniqueConstraint(
                fields=["group", "list_number"],
                condition=Q(list_number__isnull=False),
                name="cadet_unique_list_number_in_group",
            ),
            models.CheckConstraint(condition=Q(gender__in=Gender.values), name="cadet_gender_valid"),
            models.CheckConstraint(
                condition=Q(is_active=True) | ~Q(deactivation_reason=""),
                name="cadet_deactivation_reason_required",
            ),
            models.CheckConstraint(
                condition=Q(duty_exempt=False) | ~Q(duty_position=""),
                name="cadet_exempt_position_required",
            ),
        ]
        indexes = [models.Index(fields=["gender", "is_active"], name="cadet_gender_active_idx")]

    def __str__(self) -> str:
        return f"{self.short_name or self.full_name} ({self.group})" if self.group_id else self.full_name

    @property
    def full_name(self) -> str:
        return " ".join(p for p in (self.last_name, self.first_name, self.patronymic) if p)

    @property
    def on_duty(self) -> bool:
        """Naryadga chiqadi: faol va naryaddan ozod emas."""
        return self.is_active and not self.duty_exempt

    def clean(self):
        super().clean()
        if not self.is_active and not self.deactivation_reason.strip():
            raise ValidationError({"deactivation_reason": "Faolsizlantirish sababi ko‘rsatilishi shart."})

    def save(self, *args, **kwargs):
        self.last_name = normalize_apostrophes(self.last_name.strip())
        self.first_name = normalize_apostrophes(self.first_name.strip())
        self.patronymic = normalize_apostrophes(self.patronymic.strip())
        if not self.short_name:
            self.short_name = make_short_name(self.last_name, self.first_name)
        if self.is_active:
            self.deactivated_at = None
            self.deactivation_reason = ""
        elif self.deactivated_at is None:
            self.deactivated_at = timezone.now()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Joylar va o'rinlar (qulflangan, migratsiya bilan to'ldiriladi)
# ---------------------------------------------------------------------------


class Post(models.Model):
    """Navbatchilik joyi (7 ta). Interfeysda tahrirlanmaydi."""

    code = models.CharField("kod", max_length=20, unique=True)
    name = models.CharField("nomi", max_length=100)
    section_title = models.CharField("PDF bo‘lim sarlavhasi", max_length=100)
    gender = models.CharField("kim turadi", max_length=1, choices=Gender.choices)
    display_order = models.PositiveSmallIntegerField("PDF tartibi", unique=True)
    rotation_index = models.PositiveSmallIntegerField(
        "aylanish zanjiridagi o‘rni", unique=True, null=True, blank=True, help_text="Qizlar joyida bo‘sh."
    )

    class Meta:
        db_table = "post"
        ordering = ["display_order"]
        verbose_name = "navbatchilik joyi"
        verbose_name_plural = "navbatchilik joylari"
        constraints = [
            models.CheckConstraint(
                condition=(Q(gender=Gender.MALE) & Q(rotation_index__isnull=False))
                | (Q(gender=Gender.FEMALE) & Q(rotation_index__isnull=True)),
                name="post_rotation_only_for_male",
            ),
        ]

    def __str__(self) -> str:
        return self.name


class PostSlot(models.Model):
    """Joy ichidagi o'rin (lavozim). Jami 20 ta."""

    post = models.ForeignKey(Post, verbose_name="joy", on_delete=models.PROTECT, related_name="slots")
    position = models.PositiveSmallIntegerField("joy ichidagi tartibi")
    role = models.CharField("lavozim", max_length=30, choices=SlotRole.choices)
    print_label = models.CharField("PDF’dagi qator yozuvi", max_length=150)
    show_label = models.BooleanField("PDF’da yozuv ko‘rsatilsin", default=True)

    class Meta:
        db_table = "post_slot"
        ordering = ["post__display_order", "position"]
        verbose_name = "o‘rin (lavozim)"
        verbose_name_plural = "o‘rinlar (lavozimlar)"
        constraints = [
            models.UniqueConstraint(fields=["post", "position"], name="post_slot_unique_position"),
            models.CheckConstraint(condition=Q(role__in=SlotRole.values), name="post_slot_role_valid"),
        ]

    def __str__(self) -> str:
        return f"{self.post.name}: {self.get_role_display()} ({self.position})"


# ---------------------------------------------------------------------------
# Hafta va sutka
# ---------------------------------------------------------------------------


class DutyWeek(models.Model):
    """2-kurs haftasi: yakshanba 18:00 dan keyingi yakshanba 18:00 gacha (7 sutka). Admin ochadi."""

    start_date = models.DateField(
        "boshlanish sanasi (yakshanba)", unique=True, help_text="Hafta shu yakshanba soat 18:00 da boshlanadi."
    )
    note = models.CharField("izoh", max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim ochdi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    DAYS = 7

    class Meta:
        db_table = "duty_week"
        ordering = ["-start_date"]
        verbose_name = "2-kurs haftasi"
        verbose_name_plural = "2-kurs haftalari"

    def __str__(self) -> str:
        return f"{self.start_date:%d.%m.%Y} – {self.end_at.date():%d.%m.%Y}"

    @property
    def end_date(self) -> dt.date:
        """Haftaning oxirgi (7-) sutkasi boshlanadigan sana (shanba)."""
        return self.start_date + dt.timedelta(days=self.DAYS - 1)

    @property
    def start_at(self) -> dt.datetime:
        return duty_start(self.start_date)

    @property
    def end_at(self) -> dt.datetime:
        return duty_start(self.start_date + dt.timedelta(days=self.DAYS))

    @property
    def dates(self) -> list[dt.date]:
        return [self.start_date + dt.timedelta(days=i) for i in range(self.DAYS)]

    def contains(self, day: dt.date) -> bool:
        return self.start_date <= day <= self.end_date

    def clean(self):
        super().clean()
        if self.start_date is None:
            return
        if self.start_date.isoweekday() != 7:
            raise ValidationError(
                {"start_date": "Hafta yakshanba kuni (soat 18:00 da) boshlanishi kerak — tanlangan sana yakshanba emas."}
            )
        overlapping = DutyWeek.objects.filter(
            start_date__gt=self.start_date - dt.timedelta(days=self.DAYS),
            start_date__lt=self.start_date + dt.timedelta(days=self.DAYS),
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError({"start_date": f"Bu hafta boshqa hafta bilan ustma-ust tushadi: {overlapping.first()}."})


class DutyDay(models.Model):
    """Sutka: shu sanada 18:00 dan ertasi 18:00 gacha. Tarixga faqat tasdiqlangani kiradi."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Qoralama"
        APPROVED = "approved", "Tasdiqlangan"

    week = models.ForeignKey(DutyWeek, verbose_name="hafta", on_delete=models.PROTECT, related_name="days")
    date = models.DateField("sutka sanasi", unique=True, help_text="Sutka shu sanada 18:00 da boshlanadi.")
    status = models.CharField("holati", max_length=10, choices=Status.choices, default=Status.DRAFT)
    warnings = models.JSONField("ogohlantirishlar", default=list, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim tuzdi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    generated_at = models.DateTimeField("tuzilgan vaqti", null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim tasdiqladi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    approved_at = models.DateTimeField("tasdiqlangan vaqti", null=True, blank=True)
    version = models.PositiveIntegerField(
        "versiya", default=1, help_text="Har o‘zgarishda oshadi — bir vaqtda tahrirlashdan himoya."
    )

    class Meta:
        db_table = "duty_day"
        ordering = ["-date"]
        verbose_name = "sutka"
        verbose_name_plural = "sutkalar"
        constraints = [
            models.CheckConstraint(condition=Q(status__in=["draft", "approved"]), name="duty_day_status_valid"),
            models.CheckConstraint(
                condition=Q(status="draft") | Q(approved_at__isnull=False),
                name="duty_day_approved_has_time",
            ),
        ]

    def __str__(self) -> str:
        nxt = self.date + dt.timedelta(days=1)
        return f"{self.date:%d.%m.%Y} → {nxt:%d.%m.%Y} ({self.get_status_display()})"

    @property
    def start_at(self) -> dt.datetime:
        return duty_start(self.date)

    @property
    def end_at(self) -> dt.datetime:
        return duty_start(self.date + dt.timedelta(days=1))

    @property
    def is_approved(self) -> bool:
        return self.status == self.Status.APPROVED

    def clean(self):
        super().clean()
        if self.date is None or self.week_id is None:
            return
        if not self.week.contains(self.date):
            raise ValidationError(
                {"date": f"Sutka sanasi tanlangan hafta ichida bo‘lishi kerak ({self.week.start_date:%d.%m} – {self.week.end_date:%d.%m})."}
            )
        if self.status == self.Status.APPROVED and self.approved_at is None:
            raise ValidationError({"approved_at": "Tasdiqlangan sutkada tasdiqlash vaqti bo‘lishi shart."})

    @staticmethod
    def week_start_for(day: dt.date) -> dt.date:
        return engine_week_start(day)


class GroupPostAssignment(models.Model):
    """1-daraja: sutkada qaysi guruh qaysi o'g'il bolalar joyida."""

    duty_day = models.ForeignKey(
        DutyDay, verbose_name="sutka", on_delete=models.CASCADE, related_name="group_posts"
    )
    post = models.ForeignKey(
        Post, verbose_name="joy", on_delete=models.PROTECT, limit_choices_to={"gender": Gender.MALE}
    )
    group = models.ForeignKey(StudyGroup, verbose_name="guruh", on_delete=models.PROTECT)

    class Meta:
        db_table = "group_post_assignment"
        ordering = ["duty_day", "post__display_order"]
        verbose_name = "guruh → joy taqsimoti"
        verbose_name_plural = "guruh → joy taqsimotlari"
        constraints = [
            models.UniqueConstraint(fields=["duty_day", "post"], name="gpa_unique_day_post"),
            models.UniqueConstraint(fields=["duty_day", "group"], name="gpa_unique_day_group"),
        ]

    def __str__(self) -> str:
        return f"{self.post} — {self.group}"

    def clean(self):
        super().clean()
        if self.post_id and self.post.gender != Gender.MALE:
            raise ValidationError({"post": "Guruhlarga faqat o‘g‘il bolalar joylari taqsimlanadi."})


class Assignment(models.Model):
    """2-daraja: kim, qaysi sutkada, qaysi o'rinda. Tarix va statistika manbai."""

    class Source(models.TextChoices):
        AUTO = "auto", "Avtomatik"
        MANUAL = "manual", "Qo‘lda"

    duty_day = models.ForeignKey(DutyDay, verbose_name="sutka", on_delete=models.CASCADE, related_name="assignments")
    post_slot = models.ForeignKey(PostSlot, verbose_name="o‘rin", on_delete=models.PROTECT, related_name="+")
    cadet = models.ForeignKey(Cadet, verbose_name="kursant", on_delete=models.PROTECT, related_name="assignments")
    group = models.ForeignKey(
        StudyGroup,
        verbose_name="guruh (tayinlash paytida)",
        on_delete=models.PROTECT,
        related_name="+",
        help_text="Kursant keyin guruhini almashtirsa ham tarix to‘g‘ri qoladi.",
    )
    source = models.CharField("manba", max_length=10, choices=Source.choices, default=Source.AUTO)
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    class Meta:
        db_table = "assignment"
        ordering = ["duty_day", "post_slot__post__display_order", "post_slot__position"]
        verbose_name = "tayinlash"
        verbose_name_plural = "tayinlashlar"
        constraints = [
            models.UniqueConstraint(fields=["duty_day", "post_slot"], name="assignment_unique_day_slot"),
            models.UniqueConstraint(fields=["duty_day", "cadet"], name="assignment_unique_day_cadet"),
            models.CheckConstraint(condition=Q(source__in=["auto", "manual"]), name="assignment_source_valid"),
        ]
        indexes = [models.Index(fields=["cadet", "duty_day"], name="assignment_cadet_day_idx")]

    def __str__(self) -> str:
        return f"{self.post_slot.print_label}: {self.cadet}"

    def clean(self):
        super().clean()
        if not (self.cadet_id and self.post_slot_id):
            return
        if self.cadet.gender != self.post_slot.post.gender:
            raise ValidationError({"cadet": "Kursant jinsi bu joyga mos emas."})
        if self.post_slot.post.gender == Gender.MALE and self.duty_day_id:
            gpa = GroupPostAssignment.objects.filter(duty_day_id=self.duty_day_id, post_id=self.post_slot.post_id).first()
            if gpa and gpa.group_id != self.cadet.group_id:
                raise ValidationError({"cadet": f"Bu sutkada {self.post_slot.post} joyi {gpa.group} guruhiga tegishli."})

    def save(self, *args, **kwargs):
        if not self.group_id and self.cadet_id:
            self.group_id = self.cadet.group_id
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Sababli yo'qlik va jurnal
# ---------------------------------------------------------------------------


class Absence(models.Model):
    """Sababli yo'qlik. Sanalar — sutka boshlanish sanalari, ikkala chegara ham ichida."""

    class Reason(models.TextChoices):
        SICK = "kasal", "Kasal"
        LEAVE = "tatil", "Ta’til"
        EXCUSED = "sababli", "Sababli"
        OTHER = "boshqa", "Boshqa"

    cadet = models.ForeignKey(Cadet, verbose_name="kursant", on_delete=models.PROTECT, related_name="absences")
    start_date = models.DateField("birinchi sutka")
    end_date = models.DateField("oxirgi sutka (ichida)")
    reason_type = models.CharField("sabab", max_length=20, choices=Reason.choices)
    note = models.CharField("izoh", max_length=300, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim kiritdi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    class Meta:
        db_table = "absence"
        ordering = ["-start_date"]
        verbose_name = "sababli yo‘qlik"
        verbose_name_plural = "sababli yo‘qliklar"
        constraints = [
            models.CheckConstraint(condition=Q(end_date__gte=F("start_date")), name="absence_end_after_start"),
            models.CheckConstraint(condition=Q(reason_type__in=["kasal", "tatil", "sababli", "boshqa"]), name="absence_reason_valid"),
        ]
        indexes = [models.Index(fields=["cadet", "start_date", "end_date"], name="absence_cadet_dates_idx")]

    def __str__(self) -> str:
        return f"{self.cadet}: {self.start_date:%d.%m} – {self.end_date:%d.%m} ({self.get_reason_type_display()})"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "Oxirgi sutka birinchisidan oldin bo‘lishi mumkin emas."})
        if self.reason_type == self.Reason.OTHER and not self.note.strip():
            raise ValidationError({"note": "“Boshqa” sabab uchun izoh majburiy."})

    def covers(self, day: dt.date) -> bool:
        return self.start_date <= day <= self.end_date


CHANGELOG_CADET_ACTIONS = (
    "cadet_create",
    "cadet_update",
    "cadet_deactivate",
    "cadet_activate",
    "cadet_import",
    "cadet_exempt",
    "cadet_unexempt",
    "absence_add",
    "absence_change",
    "absence_delete",
)


class ChangeLog(models.Model):
    """Jurnal: kim, qachon, nima qildi, nima sababdan. O'chirilmaydi.

    Sutka amallari (`duty_day` majburiy) va kursantlar bazasidagi o'zgarishlar
    (`cadet` majburiy, `details` — nima o'zgargani) shu jadvalga yoziladi.
    """

    class Action(models.TextChoices):
        GENERATE = "generate", "Qoralama tuzildi"
        IMPORT = "import", "O‘tgan tarix kiritildi"
        REPLACE = "replace", "Almashtirildi"
        SWAP = "swap", "O‘rin almashtirildi"
        APPROVE = "approve", "Tasdiqlandi"
        REOPEN = "reopen", "Qayta ochildi"
        DRAFT_DELETE = "draft_delete", "Qoralama o‘chirildi"
        CADET_CREATE = "cadet_create", "Kursant qo‘shildi"
        CADET_UPDATE = "cadet_update", "Kursant ma’lumoti o‘zgartirildi"
        CADET_DEACTIVATE = "cadet_deactivate", "Kursant faolsizlantirildi"
        CADET_ACTIVATE = "cadet_activate", "Kursant qayta faollashtirildi"
        CADET_IMPORT = "cadet_import", "Kursant Excel’dan import qilindi"
        CADET_EXEMPT = "cadet_exempt", "Naryaddan ozod qilindi"
        CADET_UNEXEMPT = "cadet_unexempt", "Naryadga qaytarildi"
        ABSENCE_ADD = "absence_add", "Sababli holat kiritildi"
        ABSENCE_CHANGE = "absence_change", "Sababli holat o‘zgartirildi"
        ABSENCE_DELETE = "absence_delete", "Sababli holat o‘chirildi"

    REASON_REQUIRED = (
        Action.REPLACE, Action.SWAP, Action.REOPEN, Action.DRAFT_DELETE, Action.CADET_DEACTIVATE,
        Action.CADET_EXEMPT, Action.CADET_UNEXEMPT,
    )
    CADET_ACTIONS = CHANGELOG_CADET_ACTIONS

    duty_day = models.ForeignKey(
        DutyDay, verbose_name="sutka", on_delete=models.SET_NULL, related_name="changes", null=True, blank=True
    )
    day_date = models.DateField(
        "sutka sanasi", null=True, blank=True, db_index=True,
        help_text="Sutka o‘chirilsa ham jurnal saqlanadi (8-bosqich).",
    )
    cadet = models.ForeignKey(
        Cadet, verbose_name="kursant", on_delete=models.PROTECT, null=True, blank=True, related_name="changes"
    )
    details = models.TextField("nima o‘zgardi", blank=True)
    action = models.CharField("amal", max_length=20, choices=Action.choices)
    post_slot = models.ForeignKey(
        PostSlot, verbose_name="o‘rin", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    old_cadet = models.ForeignKey(
        Cadet, verbose_name="kim olindi", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    new_cadet = models.ForeignKey(
        Cadet, verbose_name="kim qo‘yildi", on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    reason = models.TextField("sabab", blank=True)
    reason_code = models.CharField(
        "sabab turi", max_length=20, blank=True, help_text="kasal / tatil / sababli / boshqa (qo‘lda tuzatishlar statistikasi uchun)"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        help_text="Bo‘sh bo‘lsa — tizim.",
    )
    created_at = models.DateTimeField("qachon", auto_now_add=True)

    class Meta:
        db_table = "change_log"
        ordering = ["-created_at", "-id"]
        verbose_name = "jurnal yozuvi"
        verbose_name_plural = "o‘zgarishlar jurnali"
        constraints = [
            models.CheckConstraint(
                condition=~Q(action__in=["replace", "swap", "reopen", "draft_delete", "cadet_deactivate", "cadet_exempt", "cadet_unexempt"])
                | ~Q(reason=""),
                name="change_log_reason_required",
            ),
            models.CheckConstraint(
                condition=(Q(action__in=CHANGELOG_CADET_ACTIONS) & Q(cadet__isnull=False))
                | (~Q(action__in=CHANGELOG_CADET_ACTIONS) & Q(day_date__isnull=False)),
                name="change_log_subject_required",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.day_date is None and self.duty_day_id:
            self.day_date = self.duty_day.date
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        subject = f"{self.day_date:%d.%m.%Y}" if self.day_date else str(self.cadet)
        return f"{self.created_at:%d.%m.%Y %H:%M} — {self.get_action_display()} ({subject})"

    def clean(self):
        super().clean()
        if self.action in self.REASON_REQUIRED and not self.reason.strip():
            raise ValidationError({"reason": "Bu amal uchun sabab majburiy."})


# ---------------------------------------------------------------------------
# Sozlamalar (yagona yozuv)
# ---------------------------------------------------------------------------


class Setting(models.Model):
    """PDF sarlavhasi va imzo uchun sozlamalar — yagona yozuv (pk = 1). Kodga yozilmaydi."""

    recipient_position = models.TextField(
        "qabul qiluvchi lavozimi",
        default="Bojxona instituti Navbatchilik\nqismi boshlig‘i, podpolkovnik",
        help_text="PDF’ning o‘ng yuqori burchagi; qatorlar Enter bilan ajratiladi.",
    )
    recipient_name = models.CharField("qabul qiluvchi ismi (jo‘nalish kelishigida)", max_length=100, default="X.Sattorovga")
    course_head_position = models.CharField("imzo: lavozim", max_length=100, default="Kurs boshlig‘i")
    course_head_rank = models.CharField("imzo: unvon", max_length=50, default="mayor")
    course_head_name = models.CharField("imzo: ism", max_length=100, default="X.Turobov")
    course_number = models.PositiveSmallIntegerField("kurs raqami", default=2)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="kim o‘zgartirdi",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    updated_at = models.DateTimeField("o‘zgartirilgan", auto_now=True)

    SINGLETON_PK = 1

    class Meta:
        db_table = "setting"
        verbose_name = "sozlamalar"
        verbose_name_plural = "sozlamalar"
        constraints = [models.CheckConstraint(condition=Q(pk=1), name="setting_singleton")]

    def __str__(self) -> str:
        return "Sozlamalar"

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Sozlamalarni o‘chirib bo‘lmaydi.")

    @classmethod
    def load(cls) -> Setting:
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return obj

    @property
    def course_title(self) -> str:
        return f"{self.course_number}-kurs ro‘yxati"


class InitialRotation(models.Model):
    """Boshlang'ich guruh → joy taqsimoti (6 guruh × 6 joy, har biri bir marta).

    Bazada birorta ham tasdiqlangan o'g'il bolalar naryadi bo'lmasa, generator
    birinchi sutkani shu taqsimot bo'yicha tuzadi. Keyin zanjir avtomatik davom etadi.
    """

    setting = models.ForeignKey(
        Setting, verbose_name="sozlamalar", on_delete=models.CASCADE, related_name="initial_rotation", default=1
    )
    post = models.OneToOneField(
        Post, verbose_name="joy", on_delete=models.PROTECT, limit_choices_to={"gender": Gender.MALE}, related_name="+"
    )
    group = models.OneToOneField(StudyGroup, verbose_name="guruh", on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "initial_rotation"
        ordering = ["post__rotation_index"]
        verbose_name = "boshlang‘ich taqsimot"
        verbose_name_plural = "boshlang‘ich taqsimot (birinchi sutka uchun)"

    def __str__(self) -> str:
        return f"{self.post} — {self.group}"

    def clean(self):
        super().clean()
        if self.post_id and self.post.gender != Gender.MALE:
            raise ValidationError({"post": "Faqat o‘g‘il bolalar joylari taqsimlanadi."})

    @classmethod
    def as_mapping(cls) -> dict[str, str] | None:
        """To'liq (6 ta) bo'lsa {joy kodi: guruh kodi}, aks holda None."""
        rows = {r.post.code: r.group.code for r in cls.objects.select_related("post", "group")}
        return rows if set(rows) == set(engine_config.ROTATION_CHAIN) else None


class LoginThrottle(models.Model):
    """Login urinishlarini cheklash: N marta xato → M daqiqa blok (settings.LOGIN_*)."""

    key = models.CharField("kalit (login)", max_length=150, unique=True)
    failures = models.PositiveSmallIntegerField("ketma-ket xatolar", default=0)
    last_failure_at = models.DateTimeField("oxirgi xato", null=True, blank=True)
    blocked_until = models.DateTimeField("blok tugash vaqti", null=True, blank=True)

    class Meta:
        db_table = "login_throttle"
        verbose_name = "login cheklovi"
        verbose_name_plural = "login cheklovlari"

    def __str__(self) -> str:
        return f"{self.key}: {self.failures} xato"

    def is_blocked(self, now=None) -> bool:
        now = now or timezone.now()
        return self.blocked_until is not None and self.blocked_until > now
