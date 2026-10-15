"""Bazadagi, lekin interfeysda ko'rinadigan o'zbekcha matnlar — tarjima katalogi uchun (13-bosqich).

Joy nomlari, PDF qator yozuvlari va guruh yo'nalishlari bazada o'zbekcha saqlanadi (PDF — doim o'zbekcha).
Interfeysda ular `{% translate post.name %}` kabi joriy tilga o'giriladi; bu ro'yxat ularni makemessages
topishi uchun kerak (gettext_noop — hech narsani o'zgartirmaydi).
"""

from django.utils.translation import gettext_noop

# Algoritm (naryad/engine) nomzodni chiqarish sabablari — almashtirish oynasida ko'rsatiladi
ENGINE_TEXTS = [
    gettext_noop("faol emas"),
    gettext_noop("sababli yo‘q"),
    gettext_noop("kecha naryadda bo‘lgan"),
    gettext_noop("bugun boshqa o‘ringa qo‘yilgan"),
    gettext_noop("faol zalyotchik — oddiy navbatda faqat 1-NO‘J yoki 1-Yotoqxonada"),
]

DB_TEXTS = [
    gettext_noop("Markaz bo‘yicha"),
    gettext_noop("Markaz bo‘yicha navbatchi yordamchisi"),
    gettext_noop("1-NO‘J bo‘yicha"),
    gettext_noop("1-NO‘J bo‘yicha navbatchi"),
    gettext_noop("1-NO‘J bo‘yicha navbatchi yordamchisi"),
    gettext_noop("1-NO‘J bo‘yicha posbon"),
    gettext_noop("2-NO‘J bo‘yicha"),
    gettext_noop("2-NO‘J bo‘yicha navbatchi"),
    gettext_noop("2-NO‘J bo‘yicha posbon"),
    gettext_noop("1-Yotoqxona bo‘yicha"),
    gettext_noop("Kurs bo‘yicha navbatchi"),
    gettext_noop("Kurs bo‘yicha posbon"),
    gettext_noop("O‘quv binosi bo‘yicha"),
    gettext_noop("O‘quv binosi bo‘yicha navbatchi"),
    gettext_noop("O‘quv binosi bo‘yicha posbon"),
    gettext_noop("Institut bo‘yicha patrul"),
    gettext_noop("Qizlar yotoqxonasi bo‘yicha"),
    gettext_noop("Qizlar yotoqxonasi bo‘yicha navbatchi"),
    gettext_noop("Qizlar yotoqxonasi bo‘yicha posbon"),
    gettext_noop("Yurisprudensiya"),
    gettext_noop("Bojxona ishi"),
]
