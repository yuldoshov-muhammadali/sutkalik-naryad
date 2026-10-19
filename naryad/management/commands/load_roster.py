"""python manage.py load_roster [--file data/roster.json]

data/roster.json dan 6 guruh va 100 kursantni yuklaydi. Qayta ishga tushirilsa
takror yozuv yaratmaydi, o'zgargan maydonlarni yangilaydi.
"""

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from naryad.importers import EXPECTED_COMPOSITION, EXPECTED_ON_DUTY, EXPECTED_ON_DUTY_TOTAL, ROSTER_PATH, load_roster


class Command(BaseCommand):
    help = "data/roster.json dan guruhlar va kursantlarni yuklaydi (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--file", type=Path, default=ROSTER_PATH, help="roster.json fayli yo‘li")

    def handle(self, *args, **options):
        path: Path = options["file"]
        if not path.exists():
            raise CommandError(f"Fayl topilmadi: {path}")
        report = load_roster(path)

        self.stdout.write(
            f"Guruhlar: {report.groups_created} ta yangi. Kursantlar: {report.created} ta yangi, "
            f"{report.updated} ta yangilandi, {report.unchanged} ta o‘zgarmadi."
        )
        self.stdout.write("")
        self.stdout.write(f"{'Guruh':<10}{'O‘g‘il':>8}{'Qiz':>6}{'Jami':>6}   Kutilgan   Naryadga chiqadi (o‘g‘il)")
        for code, (boys, girls) in report.composition.items():
            exp = EXPECTED_COMPOSITION.get(code)
            mark = "✓" if exp == (boys, girls) else "✗"
            exp_text = f"{exp[0]}/{exp[1]}" if exp else "—"
            duty = report.on_duty.get(code, 0)
            duty_mark = "✓" if EXPECTED_ON_DUTY.get(code) == duty else "✗"
            self.stdout.write(f"{code:<10}{boys:>8}{girls:>6}{boys + girls:>6}   {exp_text} {mark}     {duty} {duty_mark}")
        boys, girls = report.totals
        duty = sum(report.on_duty.values())
        self.stdout.write(
            f"{'Jami':<10}{boys:>8}{girls:>6}{boys + girls:>6}   87/13 {'✓' if (boys, girls) == (87, 13) else '✗'}"
            f"     {duty} {'✓' if duty == EXPECTED_ON_DUTY_TOTAL else '✗'}"
        )
        if report.exempt:
            self.stdout.write("")
            self.stdout.write(f"Naryadga chiqmaydi — lavozimda ({len(report.exempt)}):")
            for line in report.exempt:
                self.stdout.write(f"  {line}")

        if report.warnings:
            self.stdout.write("")
            for w in report.warnings:
                self.stdout.write(self.style.WARNING(f"Ogohlantirish: {w}"))
        else:
            self.stdout.write(self.style.SUCCESS("Tarkib CLAUDE.md 2-bo‘lim bilan mos."))
