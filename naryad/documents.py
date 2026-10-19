"""Kasallik hujjatlari (18-bosqich, CLAUDE.md 66-band): rasmni tekshirish, tozalash va saqlash.

- Fayl turi kengaytma bo'yicha emas, MAZMUNI bo'yicha (Pillow ochib ko'radi): faqat JPEG, PNG, WEBP.
- EXIF orientatsiya qo'llanadi, barcha metama'lumot (GPS va h.k.) tashlanadi: rasm qaytadan JPEG qilib yoziladi.
- Uzun tomoni ≤ 2000 px, sifat 85; kichik ko'rinish 360 px.
- Ma'lumotlar bazasida saqlanadi (Railway disk vaqtinchalik), jurnalga rasm mazmuni yozilmaydi.
"""

from __future__ import annotations

import io
import warnings

from django import forms
from django.db import transaction
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _lazy
from PIL import Image, ImageOps, UnidentifiedImageError

from .cadets import INPUT_CLASS
from .models import Absence, ChangeLog, SickDocument

MAX_DOCUMENTS = 5
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_SIDE = 2000
THUMB_SIDE = 360
JPEG_QUALITY = 85
THUMB_QUALITY = 75
MAX_PIXELS = 50_000_000  # “dekompressiya bombasi”dan himoya
ALLOWED_FORMATS = {"JPEG", "MPO", "PNG", "WEBP"}  # MPO — ba'zi telefon kameralarining JPEG'i


class DocumentError(ValueError):
    pass


def _is_heic(head: bytes) -> bool:
    return head[4:8] == b"ftyp" and head[8:12] in {b"heic", b"heix", b"hevc", b"hevx", b"mif1", b"msf1", b"heim", b"heis"}


def _encode(img: Image.Image, side: int, quality: int) -> bytes:
    copy = img.copy()
    copy.thumbnail((side, side), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    copy.save(out, "JPEG", quality=quality, optimize=True, progressive=True)  # exif berilmaydi — metama'lumot yo'q
    return out.getvalue()


def process_image(data: bytes) -> tuple[bytes, bytes, int, int]:
    """Tekshiradi va tozalaydi: (rasm, kichik rasm, eni, bo'yi). Xato bo'lsa — DocumentError (o'zbekcha/joriy til)."""
    if len(data) > MAX_UPLOAD_BYTES:
        raise DocumentError(_("Fayl juda katta: ko‘pi bilan 8 MB."))
    if _is_heic(data[:16]):
        raise DocumentError(_("HEIC formati qo‘llab-quvvatlanmaydi. Telefonda kamerani “Eng mos” (JPG) formatiga o‘tkazing yoki rasmni JPG qilib yuboring."))
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            probe = Image.open(io.BytesIO(data))
            fmt = probe.format
            if fmt not in ALLOWED_FORMATS:
                raise DocumentError(_("Faqat rasm: JPG, PNG yoki WEBP."))
            if probe.width * probe.height > MAX_PIXELS:
                raise DocumentError(_("Rasm o‘lchami juda katta."))
            probe.verify()  # buzilgan fayl
            img = Image.open(io.BytesIO(data))
            img.load()
    except DocumentError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise DocumentError(_("Faqat rasm: JPG, PNG yoki WEBP.")) from None
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, "white")
        background.paste(img, mask=img.getchannel("A"))
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")
    full = _encode(img, MAX_SIDE, JPEG_QUALITY)
    thumb = _encode(img, THUMB_SIDE, THUMB_QUALITY)
    width, height = Image.open(io.BytesIO(full)).size
    return full, thumb, width, height


class UploadForm(forms.Form):
    image = forms.FileField(label=_lazy("Rasm"), widget=forms.ClearableFileInput(attrs={"accept": "image/*"}))
    kind = forms.ChoiceField(label=_lazy("Hujjat turi"), choices=SickDocument.Kind.choices, initial=SickDocument.Kind.SICK_NOTE)
    note = forms.CharField(label=_lazy("Izoh"), max_length=200, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            f.widget.attrs.setdefault("class", INPUT_CLASS if name != "image" else "mt-1 block w-full text-sm")
        self.fields["note"].widget.attrs["placeholder"] = _("masalan: 2-varaq")

    def clean_image(self):
        upload = self.cleaned_data["image"]
        if upload.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError(_("Fayl juda katta: ko‘pi bilan 8 MB."))
        try:
            self.processed = process_image(upload.read())
        except DocumentError as exc:
            raise forms.ValidationError(str(exc)) from None
        return upload


class ReplaceForm(forms.Form):
    image = forms.FileField(label=_lazy("Yangi rasm"), widget=forms.ClearableFileInput(attrs={"accept": "image/*"}))
    clean_image = UploadForm.clean_image


def _details(absence: Absence, doc: SickDocument) -> str:
    """Jurnal uchun: hujjat turi va yozuv sanalari — rasm mazmuni yozilmaydi; doim o'zbekcha."""
    from django.utils import translation

    with translation.override("uz"):
        kind = doc.get_kind_display()
    return f"{kind}: {absence.start_date:%d.%m.%Y}–{absence.end_date:%d.%m.%Y} yozuvi"


def count_error(absence: Absence) -> str | None:
    if absence.documents.count() >= MAX_DOCUMENTS:
        return _("Bitta kasallik yozuviga ko‘pi bilan %(n)s ta rasm.") % {"n": MAX_DOCUMENTS}
    return None


@transaction.atomic
def add(absence: Absence, form: UploadForm, user) -> SickDocument:
    Absence.objects.select_for_update().filter(pk=absence.pk).first()  # bir vaqtda 6-rasm tushmasin
    error = count_error(absence)
    if error:
        raise DocumentError(error)
    full, thumb, width, height = form.processed
    doc = SickDocument.objects.create(
        absence=absence, kind=form.cleaned_data["kind"], note=form.cleaned_data["note"].strip(),
        image=full, thumb=thumb, width=width, height=height, size=len(full), created_by=user,
    )
    ChangeLog.objects.create(action=ChangeLog.Action.DOC_ADD, cadet=absence.cadet, user=user, details=_details(absence, doc))
    return doc


@transaction.atomic
def replace(doc: SickDocument, form: ReplaceForm, user) -> None:
    full, thumb, width, height = form.processed
    SickDocument.objects.filter(pk=doc.pk).update(image=full, thumb=thumb, width=width, height=height, size=len(full))
    ChangeLog.objects.create(action=ChangeLog.Action.DOC_REPLACE, cadet=doc.absence.cadet, user=user, details=_details(doc.absence, doc))


@transaction.atomic
def delete(doc: SickDocument, user) -> None:
    ChangeLog.objects.create(action=ChangeLog.Action.DOC_DELETE, cadet=doc.absence.cadet, user=user, details=_details(doc.absence, doc))
    doc.delete()


def can_view(user, absence: Absence) -> bool:
    """Admin yoki o'sha kursantning o'zi (18-bosqich). Guruh komandiri ham ko'rmaydi."""
    from . import permissions as perms

    if perms.can(user, "sick.manage"):
        return True
    return perms.can(user, "documents.own") and getattr(user, "cadet_id", None) == absence.cadet_id
