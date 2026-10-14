"""7 ta navbatchilik joyi, 20 ta o'rin va yagona sozlamalar yozuvi.

Joylar va o'rinlar soni qat'iy (CLAUDE.md 3-bo'lim) — shuning uchun ular seed
emas, migratsiya bilan yoziladi. Ma'lumot naryad/engine/config.py bilan bir xil
(tests/test_models.py buni tekshiradi).
"""

from django.db import migrations

POSTS = [
    {
        'code': 'markaz', 'name': 'Markaz bo‘yicha', 'section_title': 'Markaz bo‘yicha',
        'gender': 'M', 'display_order': 1, 'rotation_index': 0,
        'slots': [
            (1, 'navbatchi_yordamchisi', 'Markaz bo‘yicha navbatchi yordamchisi', True),
        ],
    },
    {
        'code': 'noj1', 'name': '1-NO‘J bo‘yicha', 'section_title': '1-NO‘J bo‘yicha',
        'gender': 'M', 'display_order': 2, 'rotation_index': 1,
        'slots': [
            (1, 'navbatchi', '1-NO‘J bo‘yicha navbatchi', True),
            (2, 'navbatchi_yordamchisi', '1-NO‘J bo‘yicha navbatchi yordamchisi', True),
            (3, 'posbon', '1-NO‘J bo‘yicha posbon', True),
            (4, 'posbon', '1-NO‘J bo‘yicha posbon', True),
        ],
    },
    {
        'code': 'noj2', 'name': '2-NO‘J bo‘yicha', 'section_title': '2-NO‘J bo‘yicha',
        'gender': 'M', 'display_order': 3, 'rotation_index': 2,
        'slots': [
            (1, 'navbatchi', '2-NO‘J bo‘yicha navbatchi', True),
            (2, 'posbon', '2-NO‘J bo‘yicha posbon', True),
            (3, 'posbon', '2-NO‘J bo‘yicha posbon', True),
        ],
    },
    {
        'code': 'yotoq1', 'name': '1-Yotoqxona bo‘yicha', 'section_title': '1-Yotoqxona bo‘yicha',
        'gender': 'M', 'display_order': 4, 'rotation_index': 3,
        'slots': [
            (1, 'navbatchi', 'Kurs bo‘yicha navbatchi', True),
            (2, 'posbon', 'Kurs bo‘yicha posbon', True),
            (3, 'posbon', 'Kurs bo‘yicha posbon', True),
        ],
    },
    {
        'code': 'oquv', 'name': 'O‘quv binosi bo‘yicha', 'section_title': 'O‘quv binosi bo‘yicha',
        'gender': 'M', 'display_order': 5, 'rotation_index': 4,
        'slots': [
            (1, 'navbatchi', 'O‘quv binosi bo‘yicha navbatchi', True),
            (2, 'posbon', 'O‘quv binosi bo‘yicha posbon', True),
        ],
    },
    {
        'code': 'patrul', 'name': 'Institut bo‘yicha patrul', 'section_title': 'Institut bo‘yicha patrul',
        'gender': 'M', 'display_order': 6, 'rotation_index': 5,
        'slots': [
            (1, 'posbon', 'Institut bo‘yicha patrul', True),
            (2, 'posbon', 'Institut bo‘yicha patrul', False),
            (3, 'posbon', 'Institut bo‘yicha patrul', False),
            (4, 'posbon', 'Institut bo‘yicha patrul', False),
        ],
    },
    {
        'code': 'qizlar', 'name': 'Qizlar yotoqxonasi bo‘yicha', 'section_title': 'Qizlar yotoqxonasi bo‘yicha',
        'gender': 'F', 'display_order': 7, 'rotation_index': None,
        'slots': [
            (1, 'navbatchi', 'Qizlar yotoqxonasi bo‘yicha navbatchi', True),
            (2, 'posbon', 'Qizlar yotoqxonasi bo‘yicha posbon', True),
            (3, 'posbon', 'Qizlar yotoqxonasi bo‘yicha posbon', True),
        ],
    },
]


def create_posts(apps, schema_editor):
    Post = apps.get_model("naryad", "Post")
    PostSlot = apps.get_model("naryad", "PostSlot")
    Setting = apps.get_model("naryad", "Setting")
    for data in POSTS:
        data = dict(data)
        slots = data.pop("slots")
        post, _ = Post.objects.update_or_create(code=data.pop("code"), defaults=data)
        for position, role, label, show in slots:
            PostSlot.objects.update_or_create(
                post=post, position=position, defaults={"role": role, "print_label": label, "show_label": show}
            )
    Setting.objects.get_or_create(pk=1)


def remove_posts(apps, schema_editor):
    apps.get_model("naryad", "PostSlot").objects.all().delete()
    apps.get_model("naryad", "Post").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("naryad", "0001_initial")]

    operations = [migrations.RunPython(create_posts, remove_posts)]
