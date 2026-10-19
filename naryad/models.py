"""E-NARYAD platformasi modellari (docs/01-talablar-va-sxema.md, 4-bo'lim).

Vaqt: bazada faqat sanalar saqlanadi. Sutka shu sanada 18:00 da boshlanadi,
2-kurs haftasi yakshanba 18:00 dan keyingi yakshanba 18:00 gacha (7 sutka).
Statistika saqlanmaydi — tasdiqlangan sutkalardagi Assignment dan hisoblanadi.
"""

from __future__ import annotations

import datetime as dt
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from django.utils.translation import ngettext

from naryad.engine import config as engine_config
from naryad.engine import models as em
from naryad.engine.allocator import week_start as engine_week_start
from naryad.engine.names import normalize_apostrophes
from naryad.engine.names import short_name as make_short_name


class Gender(models.TextChoices):
    MALE = em.MALE, _lazy("O‘g‘il")
    FEMALE = em.FEMALE, _lazy("Qiz")


class SlotRole(models.TextChoices):
    DUTY = em.ROLE_DUTY, _lazy("Navbatchi")
    ASSISTANT = em.ROLE_ASSISTANT, _lazy("Navbatchi yordamchisi")
    GUARD = em.ROLE_GUARD, _lazy("Posbon")


def duty_start(day: dt.date) -> dt.datetime:
    """Sutka boshlanish vaqti (Asia/Tashkent, 18:00) — timezone-aware."""
    naive = dt.datetime.combine(day, engine_config.DUTY_START_TIME)
    return timezone.make_aware(naive, timezone.get_default_timezone())


# ---------------------------------------------------------------------------
# Foydalanuvchi
# ---------------------------------------------------------------------------


class UserRole(models.TextChoices):
    ADMIN = "admin", _lazy("Admin (kurs boshlig‘i)")
    CADET = "cadet", _lazy("Kursant (faqat ko‘rish)")
    COMMANDER = "commander", _lazy("Guruh komandiri (o‘z guruhini ko‘rish)")


class AppUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Tizim foydalanuvchisi: rol va (ixtiyoriy) bog'langan kursant."""

    role = models.CharField(_lazy("rol"), max_length=10, choices=UserRole.choices, default=UserRole.CADET)
    cadet = models.OneToOneField(
        "Cadet",
        verbose_name=_lazy("kursant"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="user",
    )

    # Interfeys tili (13-bosqich): bo'sh — hali tanlamagan (o'zbekcha yoki kirishdagi cookie). Boshqa qurilmada ham shu til.
    language = models.CharField(
        _lazy("interfeys tili"), max_length=5, blank=True, default="",
        choices=[("uz", "O‘zbekcha"), ("ru", "Русский"), ("en", "English")],
    )
    must_change_password = models.BooleanField(
        _lazy("parolni almashtirishi shart"),
        default=False,
        help_text=_lazy("Belgilansa, foydalanuvchi keyingi kirishda parolini almashtirmaguncha boshqa sahifalarga o‘ta olmaydi."),
    )

    objects = AppUserManager()

    class Meta:
        db_table = "app_user"
        verbose_name = _lazy("foydalanuvchi")
        verbose_name_plural = _lazy("foydalanuvchilar")
        constraints = [
            models.CheckConstraint(condition=Q(role__in=UserRole.values), name="app_user_role_valid"),
        ]

    def clean(self):
        super().clean()
        if self.role == UserRole.CADET and not self.cadet_id and not self.is_superuser:
            raise ValidationError({"cadet": _("Kursant roli uchun kursant tanlanishi shart.")})
        if self.role == UserRole.COMMANDER:
            self.clean_commander()

    def clean_commander(self):
        """Guruh komandiri (19-bosqich, CLAUDE.md 67-band): faqat guruh komandiri lavozimidagi faol kursant,
        guruhiga bitta faol komandir akkaunti. Guruh kursantning guruhidan olinadi."""
        cadet = self.cadet
        if cadet is None:
            raise ValidationError({"cadet": _("Guruh komandiri roli uchun kursant tanlanishi shart.")})
        if not cadet.is_group_commander:
            raise ValidationError({"role": _(
                "%(name)s guruh komandiri lavozimida emas — komandir rolini faqat guruh komandiriga berish mumkin."
            ) % {"name": cadet.short_name or cadet.full_name}})
        if not cadet.is_active:
            raise ValidationError({"cadet": _("Faol bo‘lmagan kursantga komandir roli berilmaydi.")})
        if self.is_active:
            other = (
                User.objects.filter(role=UserRole.COMMANDER, is_active=True, cadet__group_id=cadet.group_id)
                .exclude(pk=self.pk).select_related("cadet").first()
            )
            if other is not None:
                raise ValidationError({"role": _("%(group)s guruhida faol komandir akkaunti allaqachon bor: %(username)s.") % {
                    "group": cadet.group.code, "username": other.username,
                }})

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
    def is_commander(self) -> bool:
        return self.role == UserRole.COMMANDER

    @property
    def is_admin_role(self) -> bool:
        return self.role == UserRole.ADMIN or self.is_superuser


# ---------------------------------------------------------------------------
# Guruh va kursant
# ---------------------------------------------------------------------------


class StudyGroup(models.Model):
    """O'quv guruhi (CLAUDE.md: group). Rotatsiya va adolat hisobi shu kesimda."""

    class Language(models.TextChoices):
        UZ = "uz", _lazy("O‘zbek")
        RU = "ru", _lazy("Rus")

    code = models.CharField(_lazy("guruh kodi"), max_length=20, unique=True, help_text=_lazy("Masalan: BI-525"))
    direction = models.CharField(_lazy("ta’lim yo‘nalishi"), max_length=100)
    language = models.CharField(_lazy("ta’lim tili"), max_length=2, choices=Language.choices, default=Language.UZ)
    display_order = models.PositiveSmallIntegerField(_lazy("tartib raqami"), unique=True)
    is_active = models.BooleanField(_lazy("faol"), default=True)

    class Meta:
        db_table = "study_group"
        ordering = ["display_order"]
        verbose_name = _lazy("guruh")
        verbose_name_plural = _lazy("guruhlar")

    def __str__(self) -> str:
        return self.code


class Cadet(models.Model):
    """Kursant. O'chirilmaydi — faqat faolsizlantiriladi (tarix saqlanadi)."""

    group = models.ForeignKey(StudyGroup, verbose_name=_lazy("guruh"), on_delete=models.PROTECT, related_name="cadets")
    last_name = models.CharField(_lazy("familiya"), max_length=60)
    first_name = models.CharField(_lazy("ism"), max_length=60)
    patronymic = models.CharField(_lazy("otasining ismi"), max_length=100, blank=True)
    gender = models.CharField(_lazy("jinsi"), max_length=1, choices=Gender.choices)
    list_number = models.PositiveSmallIntegerField(_lazy("ro‘yxatdagi raqami"), null=True, blank=True)
    short_name = models.CharField(
        _lazy("qisqa ism (PDF)"),
        max_length=60,
        blank=True,
        help_text=_lazy("Bo‘sh qoldirilsa avtomatik: Familiya + ism bosh harfi (Shavkatov Sh, G‘ayratov G‘)."),
    )
    is_active = models.BooleanField(_lazy("faol"), default=True)
    deactivated_at = models.DateTimeField(_lazy("faolsizlantirilgan vaqti"), null=True, blank=True)
    deactivation_reason = models.CharField(_lazy("faolsizlantirish sababi"), max_length=200, blank=True)
    # Komandirlar va kurs lavozimlari: faol (akkaunti ishlaydi), lekin sutkalik naryadga qo'yilmaydi
    # (CLAUDE.md 2- va 4-bo'lim, 10-bo'lim 56-band). Faqat kursant kartochkasidan, sabab bilan o'zgartiriladi.
    duty_exempt = models.BooleanField(_lazy("naryadga chiqmaydi"), default=False)
    duty_position = models.CharField(
        _lazy("lavozimi"), max_length=100, blank=True, help_text=_lazy("Masalan: Kurs starshinasi, BI-225 guruh komandiri.")
    )
    created_at = models.DateTimeField(_lazy("yaratilgan"), auto_now_add=True)
    updated_at = models.DateTimeField(_lazy("o‘zgartirilgan"), auto_now=True)

    class Meta:
        db_table = "cadet"
        ordering = ["group__display_order", "list_number", "last_name", "first_name"]
        verbose_name = _lazy("kursant")
        verbose_name_plural = _lazy("kursantlar")
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
    def is_group_commander(self) -> bool:
        """Guruh komandiri lavozimi (masalan “BI-225 guruh komandiri”); o‘rinbosar, starshina, pisar, kaptyorchik — emas."""
        return self.duty_exempt and self.duty_position.strip().lower().endswith("guruh komandiri")

    @property
    def on_duty(self) -> bool:
        """Naryadga chiqadi: faol va naryaddan ozod emas."""
        return self.is_active and not self.duty_exempt

    def clean(self):
        super().clean()
        if not self.is_active and not self.deactivation_reason.strip():
            raise ValidationError({"deactivation_reason": _("Faolsizlantirish sababi ko‘rsatilishi shart.")})

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

    code = models.CharField(_lazy("kod"), max_length=20, unique=True)
    name = models.CharField(_lazy("nomi"), max_length=100)
    section_title = models.CharField(_lazy("PDF bo‘lim sarlavhasi"), max_length=100)
    gender = models.CharField(_lazy("kim turadi"), max_length=1, choices=Gender.choices)
    display_order = models.PositiveSmallIntegerField(_lazy("PDF tartibi"), unique=True)
    rotation_index = models.PositiveSmallIntegerField(
        _lazy("aylanish zanjiridagi o‘rni"), unique=True, null=True, blank=True, help_text=_lazy("Qizlar joyida bo‘sh.")
    )

    class Meta:
        db_table = "post"
        ordering = ["display_order"]
        verbose_name = _lazy("navbatchilik joyi")
        verbose_name_plural = _lazy("navbatchilik joylari")
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

    post = models.ForeignKey(Post, verbose_name=_lazy("joy"), on_delete=models.PROTECT, related_name="slots")
    position = models.PositiveSmallIntegerField(_lazy("joy ichidagi tartibi"))
    role = models.CharField(_lazy("lavozim"), max_length=30, choices=SlotRole.choices)
    print_label = models.CharField(_lazy("PDF’dagi qator yozuvi"), max_length=150)
    show_label = models.BooleanField(_lazy("PDF’da yozuv ko‘rsatilsin"), default=True)

    class Meta:
        db_table = "post_slot"
        ordering = ["post__display_order", "position"]
        verbose_name = _lazy("o‘rin (lavozim)")
        verbose_name_plural = _lazy("o‘rinlar (lavozimlar)")
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
        _lazy("boshlanish sanasi (yakshanba)"), unique=True, help_text=_lazy("Hafta shu yakshanba soat 18:00 da boshlanadi.")
    )
    note = models.CharField(_lazy("izoh"), max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_lazy("kim ochdi"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    created_at = models.DateTimeField(_lazy("yaratilgan"), auto_now_add=True)

    DAYS = 7

    class Meta:
        db_table = "duty_week"
        ordering = ["-start_date"]
        verbose_name = _lazy("2-kurs haftasi")
        verbose_name_plural = _lazy("2-kurs haftalari")

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
                {"start_date": _("Hafta yakshanba kuni (soat 18:00 da) boshlanishi kerak — tanlangan sana yakshanba emas.")}
            )
        overlapping = DutyWeek.objects.filter(
            start_date__gt=self.start_date - dt.timedelta(days=self.DAYS),
            start_date__lt=self.start_date + dt.timedelta(days=self.DAYS),
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError(
                {"start_date": _("Bu hafta boshqa hafta bilan ustma-ust tushadi: %(week)s.") % {"week": overlapping.first()}}
            )


class DutyDay(models.Model):
    """Sutka: shu sanada 18:00 dan ertasi 18:00 gacha. Tarixga faqat tasdiqlangani kiradi."""

    class Status(models.TextChoices):
        DRAFT = "draft", _lazy("Qoralama")
        APPROVED = "approved", _lazy("Tasdiqlangan")

    week = models.ForeignKey(DutyWeek, verbose_name=_lazy("hafta"), on_delete=models.PROTECT, related_name="days")
    date = models.DateField(_lazy("sutka sanasi"), unique=True, help_text=_lazy("Sutka shu sanada 18:00 da boshlanadi."))
    status = models.CharField(_lazy("holati"), max_length=10, choices=Status.choices, default=Status.DRAFT)
    warnings = models.JSONField(_lazy("ogohlantirishlar"), default=list, blank=True)
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_lazy("kim tuzdi"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    generated_at = models.DateTimeField(_lazy("tuzilgan vaqti"), null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_lazy("kim tasdiqladi"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
    )
    approved_at = models.DateTimeField(_lazy("tasdiqlangan vaqti"), null=True, blank=True)
    version = models.PositiveIntegerField(
        _lazy("versiya"), default=1, help_text=_lazy("Har o‘zgarishda oshadi — bir vaqtda tahrirlashdan himoya.")
    )

    class Meta:
        db_table = "duty_day"
        ordering = ["-date"]
        verbose_name = _lazy("sutka")
        verbose_name_plural = _lazy("sutkalar")
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
                {
                    "date": _("Sutka sanasi tanlangan hafta ichida bo‘lishi kerak (%(start)s – %(end)s).")
                    % {"start": f"{self.week.start_date:%d.%m}", "end": f"{self.week.end_date:%d.%m}"}
                }
            )
        if self.status == self.Status.APPROVED and self.approved_at is None:
            raise ValidationError({"approved_at": _("Tasdiqlangan sutkada tasdiqlash vaqti bo‘lishi shart.")})

    @staticmethod
    def week_start_for(day: dt.date) -> dt.date:
        return engine_week_start(day)


class GroupPostAssignment(models.Model):
    """1-daraja: sutkada qaysi guruh qaysi o'g'il bolalar joyida."""

    duty_day = models.ForeignKey(
        DutyDay, verbose_name=_lazy("sutka"), on_delete=models.CASCADE, related_name="group_posts"
    )
    post = models.ForeignKey(
        Post, verbose_name=_lazy("joy"), on_delete=models.PROTECT, limit_choices_to={"gender": Gender.MALE}
    )
    group = models.ForeignKey(StudyGroup, verbose_name=_lazy("guruh"), on_delete=models.PROTECT)

    class Meta:
        db_table = "group_post_assignment"
        ordering = ["duty_day", "post__display_order"]
        verbose_name = _lazy("guruh → joy taqsimoti")
        verbose_name_plural = _lazy("guruh → joy taqsimotlari")
        constraints = [
            models.UniqueConstraint(fields=["duty_day", "post"], name="gpa_unique_day_post"),
            models.UniqueConstraint(fields=["duty_day", "group"], name="gpa_unique_day_group"),
        ]

    def __str__(self) -> str:
        return f"{self.post} — {self.group}"

    def clean(self):
        super().clean()
        if self.post_id and self.post.gender != Gender.MALE:
            raise ValidationError({"post": _("Guruhlarga faqat o‘g‘il bolalar joylari taqsimlanadi.")})


class Assignment(models.Model):
    """2-daraja: kim, qaysi sutkada, qaysi o'rinda. Tarix va statistika manbai."""

    class Source(models.TextChoices):
        AUTO = "auto", _lazy("Avtomatik")
        MANUAL = "manual", _lazy("Qo‘lda")

    class Kind(models.TextChoices):
        NORMAL = em.KIND_NORMAL, _lazy("Oddiy")
        PENALTY = em.KIND_PENALTY, _lazy("Navbatdan tashqari (jazo)")

    duty_day = models.ForeignKey(DutyDay, verbose_name=_lazy("sutka"), on_delete=models.CASCADE, related_name="assignments")
    post_slot = models.ForeignKey(PostSlot, verbose_name=_lazy("o‘rin"), on_delete=models.PROTECT, related_name="+")
    cadet = models.ForeignKey(Cadet, verbose_name=_lazy("kursant"), on_delete=models.PROTECT, related_name="assignments")
    group = models.ForeignKey(
        StudyGroup,
        verbose_name=_lazy("guruh (tayinlash paytida)"),
        on_delete=models.PROTECT,
        related_name="+",
        help_text=_lazy("Kursant keyin guruhini almashtirsa ham tarix to‘g‘ri qoladi."),
    )
    source = models.CharField(_lazy("manba"), max_length=10, choices=Source.choices, default=Source.AUTO)
    # 15-bosqich: navbatdan tashqari (jazo) naryadi — adolat hisobiga kirmaydi
    kind = models.CharField(_lazy("naryad turi"), max_length=10, choices=Kind.choices, default=Kind.NORMAL)
    penalty = models.ForeignKey(
        "Penalty", verbose_name=_lazy("zalyot"), on_delete=models.PROTECT, null=True, blank=True, related_name="assignments"
    )
    created_at = models.DateTimeField(_lazy("yaratilgan"), auto_now_add=True)

    class Meta:
        db_table = "assignment"
        ordering = ["duty_day", "post_slot__post__display_order", "post_slot__position"]
        verbose_name = _lazy("tayinlash")
        verbose_name_plural = _lazy("tayinlashlar")
        constraints = [
            models.UniqueConstraint(fields=["duty_day", "post_slot"], name="assignment_unique_day_slot"),
            models.UniqueConstraint(fields=["duty_day", "cadet"], name="assignment_unique_day_cadet"),
            models.CheckConstraint(condition=Q(source__in=["auto", "manual"]), name="assignment_source_valid"),
            models.CheckConstraint(
                condition=(Q(kind="normal") & Q(penalty__isnull=True)) | (Q(kind="penalty") & Q(penalty__isnull=False)),
                name="assignment_kind_penalty_consistent",
            ),
        ]
        indexes = [models.Index(fields=["cadet", "duty_day"], name="assignment_cadet_day_idx")]

    def __str__(self) -> str:
        return f"{self.post_slot.print_label}: {self.cadet}"

    def clean(self):
        super().clean()
        if not (self.cadet_id and self.post_slot_id):
            return
        if self.cadet.gender != self.post_slot.post.gender:
            raise ValidationError({"cadet": _("Kursant jinsi bu joyga mos emas.")})
        if self.post_slot.post.gender == Gender.MALE and self.duty_day_id:
            gpa = GroupPostAssignment.objects.filter(duty_day_id=self.duty_day_id, post_id=self.post_slot.post_id).first()
            if gpa and gpa.group_id != self.cadet.group_id:
                raise ValidationError(
                    {
                        "cadet": _("Bu sutkada %(post)s joyi %(group)s guruhiga tegishli.")
                        % {"post": self.post_slot.post, "group": gpa.group}
                    }
                )

    def save(self, *args, **kwargs):
        if not self.group_id and self.cadet_id:
            self.group_id = self.cadet.group_id
        super().save(*args, **kwargs)


class PublishedDuty(models.Model):
    """Kursantga e'lon qilingan naryad (14-bosqich): sutka tasdiqlanganda kursantlar shu yerga yoziladi.

    Tasdiq bekor qilinib, kursant almashtirilsa (yoki qoralama o'chirilsa), u shu sutkaning ro'yxatida qolmaydi —
    kursant bosh sahifasida “Naryadingiz bekor qilindi” chiqadi. Yozuv o'chirilmaydi (sutka sanasi bo'yicha).
    """

    day_date = models.DateField(_lazy("sutka sanasi"))
    cadet = models.ForeignKey(Cadet, verbose_name=_lazy("kursant"), on_delete=models.CASCADE, related_name="+")
    published_at = models.DateTimeField(_lazy("e’lon qilingan vaqti"), auto_now_add=True)

    class Meta:
        db_table = "published_duty"
        verbose_name = _lazy("e’lon qilingan naryad")
        verbose_name_plural = _lazy("e’lon qilingan naryadlar")
        constraints = [models.UniqueConstraint(fields=["day_date", "cadet"], name="published_duty_unique_day_cadet")]

    def __str__(self) -> str:
        return f"{self.day_date:%d.%m.%Y}: {self.cadet}"


# ---------------------------------------------------------------------------
# Sababli yo'qlik va jurnal
# ---------------------------------------------------------------------------


class Absence(models.Model):
    """Sababli yo'qlik. Sanalar — sutka boshlanish sanalari, ikkala chegara ham ichida."""

    class Reason(models.TextChoices):
        SICK = "kasal", _lazy("Kasal")
        LEAVE = "tatil", _lazy("Ta’til")
        EXCUSED = "sababli", _lazy("Sababli")
        OTHER = "boshqa", _lazy("Boshqa")

    cadet = models.ForeignKey(Cadet, verbose_name=_lazy("kursant"), on_delete=models.PROTECT, related_name="absences")
    start_date = models.DateField(_lazy("birinchi sutka"))
    end_date = models.DateField(_lazy("oxirgi sutka (ichida)"))
    reason_type = models.CharField(_lazy("sabab"), max_length=20, choices=Reason.choices)
    note = models.CharField(_lazy("izoh"), max_length=300, blank=True)
    # Kasallik tavsifi (17-bosqich): faqat admin ko'radi; kursant va komandir faqat sana–sanani ko'radi
    illness = models.CharField(_lazy("kasallik"), max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_lazy("kim kiritdi"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    created_at = models.DateTimeField(_lazy("yaratilgan"), auto_now_add=True)

    class Meta:
        db_table = "absence"
        ordering = ["-start_date"]
        verbose_name = _lazy("sababli yo‘qlik")
        verbose_name_plural = _lazy("sababli yo‘qliklar")
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
            raise ValidationError({"end_date": _("Oxirgi sutka birinchisidan oldin bo‘lishi mumkin emas.")})
        if self.reason_type == self.Reason.OTHER and not self.note.strip():
            raise ValidationError({"note": _("“Boshqa” sabab uchun izoh majburiy.")})

    def covers(self, day: dt.date) -> bool:
        return self.start_date <= day <= self.end_date


class SickDocumentManager(models.Manager):
    """Rasm baytlari ro'yxat so'rovlarida yuklanmaydi (18-bosqich): faqat ko'rish view'i `with_bytes()` bilan oladi."""

    def get_queryset(self):
        return super().get_queryset().defer("image", "thumb")

    def with_bytes(self):
        return super().get_queryset()


class SickDocument(models.Model):
    """Kasallik hujjati rasmi (18-bosqich, CLAUDE.md 66-band). Ma'lumotlar bazasida saqlanadi (Railway disk vaqtinchalik),
    shuning uchun zaxira nusxaga ham kiradi. Tashqi havola yo'q — faqat ruxsat tekshiradigan view orqali (UUID)."""

    class Kind(models.TextChoices):
        SICK_NOTE = "varaqa", _lazy("Kasallik varaqasi")
        INFIRMARY = "tibbiy", _lazy("Tibbiy punkt ma’lumotnomasi")
        OTHER = "boshqa", _lazy("Boshqa")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    absence = models.ForeignKey(Absence, verbose_name=_lazy("kasallik yozuvi"), on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(_lazy("hujjat turi"), max_length=10, choices=Kind.choices, default=Kind.SICK_NOTE)
    note = models.CharField(_lazy("izoh"), max_length=200, blank=True)
    image = models.BinaryField(_lazy("rasm (JPEG)"), editable=False)
    thumb = models.BinaryField(_lazy("kichik rasm (JPEG)"), editable=False)
    width = models.PositiveIntegerField(default=0, editable=False)
    height = models.PositiveIntegerField(default=0, editable=False)
    size = models.PositiveIntegerField(_lazy("hajmi (bayt)"), default=0, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_lazy("kim yukladi"), on_delete=models.PROTECT, null=True, blank=True,
        editable=False, related_name="+",
    )
    created_at = models.DateTimeField(_lazy("yuklangan"), auto_now_add=True)

    objects = SickDocumentManager()

    class Meta:
        db_table = "sick_document"
        ordering = ["created_at"]
        verbose_name = _lazy("kasallik hujjati")
        verbose_name_plural = _lazy("kasallik hujjatlari")

    def __str__(self) -> str:
        return f"{self.get_kind_display()} — {self.absence.cadet}"


class Penalty(models.Model):
    """Zalyot (15-bosqich): navbatdan tashqari jazo naryadlari. CLAUDE.md 10-bo'lim, 61-band.

    Holat: faol → (hammasi o'tilgach avtomatik) bajarildi; admin sabab bilan bekor qilishi mumkin.
    Bir kursantda bitta faol zalyot; yangisi qo'shilsa, soni mavjudiga qo'shiladi.
    O'tilgan naryadlar — tasdiqlangan sutkalardagi jazo o'rinlari (Assignment.kind = penalty).
    """

    class Reason(models.TextChoices):
        BREACH = "tartib", _lazy("Ichki tartib-qoidalarni buzish")
        SLEEP = "uxlash", _lazy("Naryadda uxlab qolish")
        OTHER = "boshqa", _lazy("Boshqa")

    class Status(models.TextChoices):
        ACTIVE = "active", _lazy("Faol")
        DONE = "done", _lazy("Bajarildi")
        CANCELLED = "cancelled", _lazy("Bekor qilindi")

    MAX_ADD = 10  # bitta kiritishda 1–10 ta

    cadet = models.ForeignKey(Cadet, verbose_name=_lazy("kursant"), on_delete=models.PROTECT, related_name="penalties")
    reason_type = models.CharField(_lazy("sabab turi"), max_length=10, choices=Reason.choices)
    note = models.TextField(_lazy("izoh"))
    order_date = models.DateField(_lazy("buyruq/tanbeh sanasi"))
    count = models.PositiveSmallIntegerField(_lazy("jazo naryadlari soni (jami)"), validators=[MinValueValidator(1)])
    status = models.CharField(_lazy("holati"), max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_lazy("kim kiritdi"), on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    created_at = models.DateTimeField(_lazy("kiritilgan vaqti"), auto_now_add=True)
    finished_at = models.DateTimeField(_lazy("yakunlangan vaqti"), null=True, blank=True)
    cancel_reason = models.TextField(_lazy("bekor qilish sababi"), blank=True)
    # 20-bosqich: komandir kiritgan (yoki qo'shgan) zalyot admin ko'rib chiqmaguncha “Yangi”
    reviewed_at = models.DateTimeField(_lazy("ko‘rib chiqilgan vaqti"), null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_lazy("ko‘rib chiqdi"), on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        db_table = "penalty"
        ordering = ["status", "order_date", "pk"]
        verbose_name = _lazy("zalyot")
        verbose_name_plural = _lazy("zalyotlar (navbatdan tashqari naryadlar)")
        constraints = [
            models.UniqueConstraint(fields=["cadet"], condition=Q(status="active"), name="penalty_one_active_per_cadet"),
            models.CheckConstraint(condition=Q(count__gte=1), name="penalty_count_positive"),
            models.CheckConstraint(condition=Q(status__in=["active", "done", "cancelled"]), name="penalty_status_valid"),
        ]

    def __str__(self) -> str:
        return f"{self.cadet} — {self.get_reason_type_display()} ({self.count})"

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE

    @property
    def is_new(self) -> bool:
        return self.reviewed_at is None



    @property
    def served(self) -> int:
        """O'tilgan jazo naryadlari: faqat TASDIQLANGAN sutkalardagilari."""
        if hasattr(self, "served_count"):
            return self.served_count
        return self.assignments.filter(duty_day__status=DutyDay.Status.APPROVED).count()

    @property
    def remaining(self) -> int:
        return max(0, self.count - self.served)



class PenaltyEntry(models.Model):
    """Har bir zalyot kiritish (20-bosqich): kim, qachon, nechta. Bir faol zalyotga bir nechta kiritish qo'shilishi mumkin.
    “Kim kiritdi” hisobi, davr filtri va takroriy yuborishni aniqlash shu yozuvlardan."""

    penalty = models.ForeignKey(Penalty, verbose_name=_lazy("zalyot"), on_delete=models.CASCADE, related_name="entries")
    cadet = models.ForeignKey(Cadet, verbose_name=_lazy("kursant"), on_delete=models.PROTECT, related_name="+")
    reason_type = models.CharField(_lazy("sabab turi"), max_length=10, choices=Penalty.Reason.choices)
    note = models.TextField(_lazy("izoh"))
    order_date = models.DateField(_lazy("buyruq/tanbeh sanasi"))
    count = models.PositiveSmallIntegerField(_lazy("jazo naryadlari soni"), validators=[MinValueValidator(1)])
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_lazy("kim kiritdi"), on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    by_commander = models.BooleanField(_lazy("komandir kiritgan"), default=False)
    created_at = models.DateTimeField(_lazy("kiritilgan vaqti"), auto_now_add=True)

    class Meta:
        db_table = "penalty_entry"
        ordering = ["created_at", "pk"]
        verbose_name = _lazy("zalyot kiritish")
        verbose_name_plural = _lazy("zalyot kiritishlar")
        indexes = [models.Index(fields=["cadet", "order_date", "reason_type", "created_at"], name="penalty_entry_dedup_idx")]

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
    "sick_add",
    "sick_edit",
    "sick_extend",
    "sick_recover",
    "sick_delete",
    "doc_add",
    "doc_replace",
    "doc_delete",
    "penalty_add",
    "penalty_cancel",
    "penalty_done",
    "penalty_resume",
    "penalty_edit",
    "penalty_review",
)


class ChangeLog(models.Model):
    """Jurnal: kim, qachon, nima qildi, nima sababdan. O'chirilmaydi.

    Sutka amallari (`duty_day` majburiy) va kursantlar bazasidagi o'zgarishlar
    (`cadet` majburiy, `details` — nima o'zgargani) shu jadvalga yoziladi.
    """

    class Action(models.TextChoices):
        GENERATE = "generate", _lazy("Qoralama tuzildi")
        IMPORT = "import", _lazy("O‘tgan tarix kiritildi")
        REPLACE = "replace", _lazy("Almashtirildi")
        SWAP = "swap", _lazy("O‘rin almashtirildi")
        APPROVE = "approve", _lazy("Tasdiqlandi")
        REOPEN = "reopen", _lazy("Qayta ochildi")
        DRAFT_DELETE = "draft_delete", _lazy("Qoralama o‘chirildi")
        CADET_CREATE = "cadet_create", _lazy("Kursant qo‘shildi")
        CADET_UPDATE = "cadet_update", _lazy("Kursant ma’lumoti o‘zgartirildi")
        CADET_DEACTIVATE = "cadet_deactivate", _lazy("Kursant faolsizlantirildi")
        CADET_ACTIVATE = "cadet_activate", _lazy("Kursant qayta faollashtirildi")
        CADET_IMPORT = "cadet_import", _lazy("Kursant Excel’dan import qilindi")
        CADET_EXEMPT = "cadet_exempt", _lazy("Naryadga chiqmaydi deb belgilandi")
        CADET_UNEXEMPT = "cadet_unexempt", _lazy("Naryadga qaytarildi")
        ABSENCE_ADD = "absence_add", _lazy("Sababli holat kiritildi")
        ABSENCE_CHANGE = "absence_change", _lazy("Sababli holat o‘zgartirildi")
        ABSENCE_DELETE = "absence_delete", _lazy("Sababli holat o‘chirildi")
        SICK_ADD = "sick_add", _lazy("Kasallar ro‘yxatiga kiritildi")
        SICK_EDIT = "sick_edit", _lazy("Kasallik yozuvi tahrirlandi")
        SICK_EXTEND = "sick_extend", _lazy("Kasallik muddati uzaytirildi")
        SICK_RECOVER = "sick_recover", _lazy("Sog‘ayib qaytdi")
        SICK_DELETE = "sick_delete", _lazy("Kasallik yozuvi o‘chirildi")
        DOC_ADD = "doc_add", _lazy("Kasallik hujjati yuklandi")
        DOC_REPLACE = "doc_replace", _lazy("Kasallik hujjati almashtirildi")
        DOC_DELETE = "doc_delete", _lazy("Kasallik hujjati o‘chirildi")
        PENALTY_ADD = "penalty_add", _lazy("Zalyot kiritildi")
        PENALTY_CANCEL = "penalty_cancel", _lazy("Zalyot bekor qilindi")
        PENALTY_DONE = "penalty_done", _lazy("Zalyot bajarildi")
        PENALTY_RESUME = "penalty_resume", _lazy("Zalyot qayta faollashdi")
        PENALTY_EDIT = "penalty_edit", _lazy("Zalyot tahrirlandi")
        PENALTY_REVIEW = "penalty_review", _lazy("Zalyot ko‘rib chiqildi")
        TEST_DATA_CLEARED = "test_data_cleared", _lazy("Sinov ma’lumotlari tozalandi")

    REASON_REQUIRED = (
        Action.REPLACE, Action.SWAP, Action.REOPEN, Action.DRAFT_DELETE, Action.CADET_DEACTIVATE,
        Action.CADET_EXEMPT, Action.CADET_UNEXEMPT, Action.PENALTY_ADD, Action.PENALTY_CANCEL,
    )
    CADET_ACTIONS = CHANGELOG_CADET_ACTIONS

    duty_day = models.ForeignKey(
        DutyDay, verbose_name=_lazy("sutka"), on_delete=models.SET_NULL, related_name="changes", null=True, blank=True
    )
    day_date = models.DateField(
        _lazy("sutka sanasi"), null=True, blank=True, db_index=True,
        help_text=_lazy("Sutka o‘chirilsa ham jurnal saqlanadi (8-bosqich)."),
    )
    cadet = models.ForeignKey(
        Cadet, verbose_name=_lazy("kursant"), on_delete=models.PROTECT, null=True, blank=True, related_name="changes"
    )
    details = models.TextField(_lazy("nima o‘zgardi"), blank=True)
    action = models.CharField(_lazy("amal"), max_length=20, choices=Action.choices)
    post_slot = models.ForeignKey(
        PostSlot, verbose_name=_lazy("o‘rin"), on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    old_cadet = models.ForeignKey(
        Cadet, verbose_name=_lazy("kim olindi"), on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    new_cadet = models.ForeignKey(
        Cadet, verbose_name=_lazy("kim qo‘yildi"), on_delete=models.PROTECT, null=True, blank=True, related_name="+"
    )
    reason = models.TextField(_lazy("sabab"), blank=True)
    reason_code = models.CharField(
        _lazy("sabab turi"), max_length=20, blank=True, help_text=_lazy("kasal / tatil / sababli / boshqa (qo‘lda tuzatishlar statistikasi uchun)")
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_lazy("kim"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        help_text=_lazy("Bo‘sh bo‘lsa — tizim."),
    )
    created_at = models.DateTimeField(_lazy("qachon"), auto_now_add=True)

    class Meta:
        db_table = "change_log"
        ordering = ["-created_at", "-id"]
        verbose_name = _lazy("jurnal yozuvi")
        verbose_name_plural = _lazy("o‘zgarishlar jurnali")
        constraints = [
            models.CheckConstraint(
                condition=~Q(action__in=["replace", "swap", "reopen", "draft_delete", "cadet_deactivate", "cadet_exempt", "cadet_unexempt",
                                         "penalty_add", "penalty_cancel"])
                | ~Q(reason=""),
                name="change_log_reason_required",
            ),
            models.CheckConstraint(
                condition=(Q(action__in=CHANGELOG_CADET_ACTIONS) & Q(cadet__isnull=False))
                | (~Q(action__in=CHANGELOG_CADET_ACTIONS) & Q(day_date__isnull=False))
                | Q(action="test_data_cleared"),  # 20-bosqich: tozalash yozuvi — na kursant, na sutka
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
            raise ValidationError({"reason": _("Bu amal uchun sabab majburiy.")})


# ---------------------------------------------------------------------------
# Sozlamalar (yagona yozuv)
# ---------------------------------------------------------------------------


class Setting(models.Model):
    """PDF sarlavhasi va imzo uchun sozlamalar — yagona yozuv (pk = 1). Kodga yozilmaydi."""

    recipient_position = models.TextField(
        _lazy("qabul qiluvchi lavozimi"),
        default="Bojxona instituti Navbatchilik\nqismi boshlig‘i, podpolkovnik",
        help_text=_lazy("PDF’ning o‘ng yuqori burchagi; qatorlar Enter bilan ajratiladi."),
    )
    recipient_name = models.CharField(_lazy("qabul qiluvchi ismi (jo‘nalish kelishigida)"), max_length=100, default="X.Sattorovga")
    course_head_position = models.CharField(_lazy("imzo: lavozim"), max_length=100, default="Kurs boshlig‘i")
    course_head_rank = models.CharField(_lazy("imzo: unvon"), max_length=50, default="mayor")
    course_head_name = models.CharField(_lazy("imzo: ism"), max_length=100, default="X.Turobov")
    course_number = models.PositiveSmallIntegerField(_lazy("kurs raqami"), default=2)
    approval_lead_hours = models.PositiveSmallIntegerField(
        _lazy("tasdiqlash muddati (soat)"),
        default=24,
        validators=[MinValueValidator(1), MaxValueValidator(168)],
        help_text=_lazy(
            "Sutka boshlanishidan (18:00) necha soat oldin tasdiqlangan bo‘lishi kerak. 24 — bir kun oldin, 18:00 gacha."
        ),
    )
    penalty_per_post = models.PositiveSmallIntegerField(
        _lazy("bir joyga zalyotchiklar (sutkada)"),
        default=engine_config.PENALTY_PER_POST_DEFAULT,
        validators=[MinValueValidator(1), MaxValueValidator(2)],
        help_text=_lazy("1-NO‘J va 1-Yotoqxonada bir sutkada ko‘pi bilan nechta zalyotchik posbon bo‘ladi (1 yoki 2)."),
    )
    # 20-bosqich: guruh komandiri zalyot kiritishi
    commander_penalty_max = models.PositiveSmallIntegerField(
        _lazy("komandir kirita oladigan eng ko‘p jazo naryadlari"), default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_lazy("Bitta kiritishda (admin uchun 1–10 qoladi)."),
    )
    commander_order_max_age_days = models.PositiveSmallIntegerField(
        _lazy("tanbeh sanasi necha kundan eski bo‘lmasin (komandir)"), default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
    )
    commander_daily_limit = models.PositiveSmallIntegerField(
        _lazy("komandir bir kunda kirita oladigan zalyotlar"), default=5,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_lazy("kim o‘zgartirdi"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )
    updated_at = models.DateTimeField(_lazy("o‘zgartirilgan"), auto_now=True)

    SINGLETON_PK = 1

    class Meta:
        db_table = "setting"
        verbose_name = _lazy("sozlamalar")
        verbose_name_plural = _lazy("sozlamalar")
        constraints = [models.CheckConstraint(condition=Q(pk=1), name="setting_singleton")]

    def __str__(self) -> str:
        return _("Sozlamalar")

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_("Sozlamalarni o‘chirib bo‘lmaydi."))

    @classmethod
    def load(cls) -> Setting:
        obj, _created = cls.objects.get_or_create(pk=cls.SINGLETON_PK)
        return obj

    @property
    def course_title(self) -> str:
        return f"{self.course_number}-kurs ro‘yxati"


class PrepNote(models.Model):
    """Joy bo'yicha tayyorgarlik eslatmasi (14-bosqich): kursant o'z naryadi kartochkasida ko'radi.

    Uch tilda kiritiladi; joriy tildagisi bo'sh bo'lsa — o'zbekchasi, u ham bo'sh bo'lsa — ko'rsatilmaydi.
    """

    setting = models.ForeignKey(
        Setting, verbose_name=_lazy("sozlamalar"), on_delete=models.CASCADE, related_name="prep_notes", default=1
    )
    post = models.OneToOneField(Post, verbose_name=_lazy("joy"), on_delete=models.CASCADE, related_name="prep_note")
    text_uz = models.CharField(_lazy("eslatma (o‘zbekcha)"), max_length=300, blank=True)
    text_ru = models.CharField(_lazy("eslatma (ruscha)"), max_length=300, blank=True)
    text_en = models.CharField(_lazy("eslatma (inglizcha)"), max_length=300, blank=True)

    class Meta:
        db_table = "prep_note"
        ordering = ["post__display_order"]
        verbose_name = _lazy("tayyorgarlik eslatmasi")
        verbose_name_plural = _lazy("tayyorgarlik eslatmalari (kursant o‘z naryadi kartochkasida ko‘radi)")

    def __str__(self) -> str:
        return str(self.post)

    def text(self, lang: str) -> str:
        return (getattr(self, f"text_{lang}", "") or self.text_uz).strip()


class InitialRotation(models.Model):
    """Boshlang'ich guruh → joy taqsimoti (6 guruh × 6 joy, har biri bir marta).

    Bazada birorta ham tasdiqlangan o'g'il bolalar naryadi bo'lmasa, generator
    birinchi sutkani shu taqsimot bo'yicha tuzadi. Keyin zanjir avtomatik davom etadi.
    """

    setting = models.ForeignKey(
        Setting, verbose_name=_lazy("sozlamalar"), on_delete=models.CASCADE, related_name="initial_rotation", default=1
    )
    post = models.OneToOneField(
        Post, verbose_name=_lazy("joy"), on_delete=models.PROTECT, limit_choices_to={"gender": Gender.MALE}, related_name="+"
    )
    group = models.OneToOneField(StudyGroup, verbose_name=_lazy("guruh"), on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "initial_rotation"
        ordering = ["post__rotation_index"]
        verbose_name = _lazy("boshlang‘ich taqsimot")
        verbose_name_plural = _lazy("boshlang‘ich taqsimot (birinchi sutka uchun)")

    def __str__(self) -> str:
        return f"{self.post} — {self.group}"

    def clean(self):
        super().clean()
        if self.post_id and self.post.gender != Gender.MALE:
            raise ValidationError({"post": _("Faqat o‘g‘il bolalar joylari taqsimlanadi.")})

    @classmethod
    def as_mapping(cls) -> dict[str, str] | None:
        """To'liq (6 ta) bo'lsa {joy kodi: guruh kodi}, aks holda None."""
        rows = {r.post.code: r.group.code for r in cls.objects.select_related("post", "group")}
        return rows if set(rows) == set(engine_config.ROTATION_CHAIN) else None


class LoginThrottle(models.Model):
    """Login urinishlarini cheklash: N marta xato → M daqiqa blok (settings.LOGIN_*)."""

    key = models.CharField(_lazy("kalit (login)"), max_length=150, unique=True)
    failures = models.PositiveSmallIntegerField(_lazy("ketma-ket xatolar"), default=0)
    last_failure_at = models.DateTimeField(_lazy("oxirgi xato"), null=True, blank=True)
    blocked_until = models.DateTimeField(_lazy("blok tugash vaqti"), null=True, blank=True)

    class Meta:
        db_table = "login_throttle"
        verbose_name = _lazy("login cheklovi")
        verbose_name_plural = _lazy("login cheklovlari")

    def __str__(self) -> str:
        return ngettext("%(key)s: %(n)s xato", "%(key)s: %(n)s xato", self.failures) % {"key": self.key, "n": self.failures}

    def is_blocked(self, now=None) -> bool:
        now = now or timezone.now()
        return self.blocked_until is not None and self.blocked_until > now
