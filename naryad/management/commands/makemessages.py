"""makemessages: loyihada `gettext_lazy as _lazy` qisqartmasi ishlatiladi — xgettext uni ham tanisin (13-bosqich).

    python manage.py makemessages -l ru -l en --no-obsolete --no-location -i "tests/*" -i "scripts/*" \
        -i "naryad/engine/*" -i "naryad/migrations/*" -i "docs/*" -i "staticfiles/*" -i "assets/*" -i "templates/naryad/pdf/*"
"""

from django.core.management.commands import makemessages


class Command(makemessages.Command):
    xgettext_options = makemessages.Command.xgettext_options + ["--keyword=_lazy"]
