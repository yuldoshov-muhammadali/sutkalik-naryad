"""python manage.py create_cadet_accounts [--output-dir data]

Har bir faol kursantga login (familiya.ism) va vaqtinchalik parol yaratadi va
chop etish uchun data/akkauntlar_<sana>.xlsx ga yozadi. Mavjud akkauntlarga tegmaydi.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from naryad.accounts import create_cadet_accounts


class Command(BaseCommand):
    help = "Faol kursantlarga akkaunt va vaqtinchalik parol yaratadi (xlsx ga yozadi)."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", type=Path, default=Path(settings.BASE_DIR) / "data")

    def handle(self, *args, **options):
        report = create_cadet_accounts(options["output_dir"])
        self.stdout.write(f"Yangi akkauntlar: {len(report.created)} ta. Akkaunti borlar (tegilmadi): {report.skipped} ta.")
        if report.file:
            self.stdout.write(self.style.SUCCESS(f"Login va parollar: {report.file}"))
            self.stdout.write(
                self.style.WARNING("Bu faylda ochiq parollar bor: chop etgach o‘chiring, hech qayerga yuklamang (git’da e’tiborsiz qoldirilgan).")
            )
        else:
            self.stdout.write("Yangi akkaunt yaratilmadi — fayl yozilmadi.")
