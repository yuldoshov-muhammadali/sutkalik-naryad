"""python manage.py import_history <fayl.xlsx|.csv> [--dry-run]

Qog'ozdagi o'tgan sutkalarni kiritadi. Ustunlar: sana, joy, lavozim, kursant, guruh.
Bitta ham xato bo'lsa — hech narsa yozilmaydi va xatolar qator raqami bilan chiqariladi.
Shablon: data/tarix_shablon.xlsx, namuna: data/tarix_namuna.xlsx.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from naryad.importers import ImportFailed, import_history


class Command(BaseCommand):
    help = "Qog‘ozdagi o‘tgan sutkalarni (xlsx/csv) tasdiqlangan holda import qiladi."

    def add_arguments(self, parser):
        parser.add_argument("file", type=Path, help="xlsx yoki csv fayl")
        parser.add_argument("--dry-run", action="store_true", help="bazaga yozmasdan faqat tekshirish")

    def handle(self, *args, **options):
        path: Path = options["file"]
        dry_run: bool = options["dry_run"]
        if not path.exists():
            raise CommandError(f"Fayl topilmadi: {path}")
        try:
            report = import_history(path, dry_run=dry_run)
        except ImportFailed as exc:
            r = exc.report
            self.stderr.write(self.style.ERROR(f"Import bajarilmadi — {len(r.errors)} ta xato (bazaga hech narsa yozilmadi):"))
            for e in r.errors:
                self.stderr.write(f"  • {e}")
            raise CommandError("Xatolarni tuzatib, qayta ishga tushiring.") from None

        days = ", ".join(f"{d:%d.%m.%Y}" for d in report.days)
        prefix = "[--dry-run] Tekshiruv muvaffaqiyatli, bazaga yozilmadi." if dry_run else "Import muvaffaqiyatli."
        self.stdout.write(self.style.SUCCESS(prefix))
        self.stdout.write(f"Qatorlar: {report.rows_read}. Sutkalar ({len(report.days)} ta): {days}")
        for w in report.warnings:
            self.stdout.write(self.style.WARNING(f"Ogohlantirish: {w}"))
        if report.weeks_created:
            weeks = ", ".join(f"{w:%d.%m.%Y}" for w in report.weeks_created)
            self.stdout.write(f"{'Yaratiladigan' if dry_run else 'Yaratilgan'} 2-kurs haftalari (yakshanba): {weeks}")
