"""python manage.py clear_test_data [--dry-run] [--backup-dir DIR]

Sinov ma'lumotlarini to'liq tozalaydi (CLAUDE.md 69-band): naryadlar, statistika, zalyotlar va jurnal 0 dan.
Kursantlar, akkauntlar, sozlamalar, boshlang'ich taqsimot, sababli holatlar va kasallar qoladi.
Avval avtomatik zaxira (.json.gz); zaxira bo'lmasa o'chirilmaydi. Ikki so'z bilan tasdiqlanadi.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from naryad import cleanup


class Command(BaseCommand):
    help = "Sinov ma'lumotlarini tozalaydi (naryadlar, zalyotlar, jurnal) — avval zaxira."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Faqat ko‘rib chiqish, hech narsa o‘chirilmaydi.")
        parser.add_argument("--backup-dir", type=Path, default=None)
        parser.add_argument("--confirm", default=None, help=f"Birinchi so‘z: {cleanup.WORD_1}")
        parser.add_argument("--confirm2", default=None, help=f"Ikkinchi so‘z: {cleanup.WORD_2}")

    def handle(self, *args, **options):
        p = cleanup.preview()
        w = self.stdout.write
        w("O‘chadi:")
        w(f"  haftalar: {p.weeks}")
        w(f"  sutkalar: {p.days} (tasdiqlangan {p.days_approved}, qoralama {p.days_draft}; import qilingan {p.days_imported}, platformada tuzilgan {p.days_platform})")
        w(f"  naryad yozuvlari: {p.assignments} (shundan jazo naryadi {p.assignments_penalty}), guruh → joy: {p.group_posts}, e’lon qilingan: {p.published}")
        w(f"  zalyotlar: {p.penalties} (kiritishlar {p.penalty_entries})")
        w(f"  jurnal yozuvlari: {p.changelog}")
        top = sorted(p.cadets, key=lambda r: -r[1])[:5]
        w("  eng ko‘p turganlar (oldin → keyin): " + ", ".join(f"{c.short_name} {n} → 0" for c, n, _ in top))
        w("Qoladi: kursantlar, guruhlar, joylar, akkauntlar, sozlamalar, boshlang‘ich taqsimot, sababli holatlar, kasallar.")
        if options["dry_run"]:
            w(self.style.SUCCESS("Ko‘rib chiqish (--dry-run): hech narsa o‘zgarmadi."))
            return
        if p.nothing_to_delete:
            w("O‘chiradigan sinov ma’lumoti yo‘q — allaqachon tozalangan.")
            return
        w(self.style.WARNING("Naryadlar, statistika, zalyotlar va jurnal butunlay o‘chadi. Qaytarib bo‘lmaydi (faqat zaxira nusxadan). "
                             "Navbat zanjiri boshidan boshlanadi."))
        word_1 = options["confirm"] if options["confirm"] is not None else input(f"Davom etish uchun {cleanup.WORD_1} deb yozing: ")
        word_2 = options["confirm2"] if options["confirm2"] is not None else input(f"Yana bir bor: {cleanup.WORD_2} deb yozing: ")
        try:
            result = cleanup.clear(None, word_1, word_2, p.token, options["backup_dir"])
        except cleanup.CleanupError as exc:
            raise CommandError(str(exc)) from exc
        w(self.style.SUCCESS(f"Tozalandi. Zaxira: {result.backup}"))
        w(f"Tiklash: python manage.py migrate && python manage.py flush --no-input && python manage.py loaddata {result.backup}")
