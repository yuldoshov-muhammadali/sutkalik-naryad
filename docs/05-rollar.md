# Rollar va ruxsatlar

> Manba: `naryad/permissions.py` dagi `PERMISSIONS` jadvali — ruxsatlar faqat shu yerda belgilanadi.
> `tests/test_ui.py::test_roles_doc_matches_permission_table` bu hujjat jadval bilan bir xilligini tekshiradi.

## Rollar

Platformada **uch rol** bor (19-bosqichdan: admin, kursant, guruh komandiri). Sutkalik naryad ro‘yxatini **dastur o‘zi tuzadi** (algoritm, `docs/02-algoritm.md`), shuning uchun alohida “tuzuvchi” roli yo‘q (CLAUDE.md 10-bo‘lim, 26-band). 10-bosqichda qayta tasdiqlandi: sutkani tuzish, tuzatish va tasdiqlashni **faqat admin** qiladi, tuzuvchi roli qaytarilmaydi (50-band).

| Rol | Kim | Qisqacha |
|---|---|---|
| **Admin** (`admin`) | Kurs boshlig‘i | Hammasi: haftani ochish, “qoralama tuzish” tugmasi (ro‘yxatni dastur tuzadi), sabab bilan qo‘lda tuzatish, sutkani tasdiqlash va qayta ochish, kursantlar bazasi, sozlamalar, boshqaruv paneli. Superuser ham admin hisoblanadi. |
| **Kursant** (`cadet`) | Har bir kursant | Bosh sahifada navbatdagi tasdiqlangan naryadi (sana, joy, lavozim, hisoblagich) va “Mening tarixim”. “Tasdiqlangan naryadlar”: faqat **tasdiqlangan** sutkalar ro‘yxati, sahifasi (o‘qish uchun, o‘z o‘rni ajratilgan) va rasmiy PDF (16-bosqich, CLAUDE.md 63-band). Qoralamalar, jurnal, sabablar, boshqa kursantlarning kartochkalari, statistika, sababli holatlar va zalyotchiklar — yopiq (403). |
| **Guruh komandiri** (`commander`) | 6 ta guruh komandiri (19-bosqich, CLAUDE.md 67-band) | Kursantning barcha imkoniyatlari + “Mening guruhim”: faqat o‘z guruhi (guruh kursantning guruhidan olinadi), faqat tasdiqlangan sutkalar, kasallik — faqat “kasal, sana–sana”. Hech narsa kiritmaydi; tavsif, hujjat, sabablar, zalyot, statistika, jurnal va admin bo‘limlari — yopiq (403). Boshqa guruh kursanti — 404. |

## Ruxsatlar jadvali

| Amal | Kalit | Admin | Kursant | Guruh komandiri |
|---|---|---|---|---|
| Bosh sahifa (rolga qarab) | `home.view` | ✅ | ✅ | ✅ |
| O‘z parolini almashtirish | `account.password_change` | ✅ | ✅ | ✅ |
| Tasdiqlangan sutkalarni ko‘rish (kursant — faqat o‘qish uchun) | `day.view_approved` | ✅ | ✅ | ✅ |
| O‘z kartochkasi va naryad tarixini ko‘rish | `history.own` | — | ✅ | ✅ |
| Mening guruhim: o‘z guruhi kursantlarining tasdiqlangan naryadlari va “kasal, sana–sana” (faqat ko‘rish) | `group.view` | — | — | ✅ |
| 2-kurs haftalari va sutkalar holatini ko‘rish | `week.view` | ✅ | — | — |
| 2-kurs haftasini ochish | `week.open` | ✅ | — | — |
| Qoralama sutkalarni ko‘rish | `day.view_draft` | ✅ | — | — |
| Sutka qoralamasini tuzish (ro‘yxatni dastur avtomatik tuzadi) | `day.generate` | ✅ | — | — |
| Qoralamani qo‘lda tuzatish (sabab majburiy, jurnalga yoziladi) | `day.edit` | ✅ | — | — |
| Sutkani tasdiqlash | `day.approve` | ✅ | — | — |
| Tasdiqlangan sutkani qayta ochish (sabab majburiy) | `day.reopen` | ✅ | — | — |
| Sababli yo‘qliklarni (kasal, ta’til) kiritish | `absence.manage` | ✅ | — | — |
| Kasallar ro‘yxati: kasallikni kiritish, tahrirlash, muddatni uzaytirish (tavsif bilan), hujjat rasmlari | `sick.manage` | ✅ | — | — |
| O‘z kasallik hujjatlarini (rasmlarini) ko‘rish — faqat ko‘rish | `documents.own` | — | ✅ | ✅ |
| O‘z guruhi kursantiga zalyot kiritish va o‘z guruhi zalyotlarini ko‘rish (tahrir va bekor qilish — yo‘q) | `penalty.group` | — | — | ✅ |
| Zalyotchiklar: jazo naryadini kiritish, tahrirlash, bekor qilish, ko‘rib chiqish va zalyot hisobi | `penalty.manage` | ✅ | — | — |
| Har qanday kursant kartochkasi, tarixi va statistika | `history.all` | ✅ | — | — |
| PDF yuklab olish va chop etish (kursant — faqat tasdiqlangan sutkalar) | `pdf.export` | ✅ | ✅ | ✅ |
| Kursantlar ro‘yxatini ko‘rish (filtr, qidiruv) | `cadets.view` | ✅ | — | — |
| Kursant qo‘shish, tahrirlash, faolsizlantirish, Excel import, akkauntlar | `cadets.manage` | ✅ | — | — |
| Sozlamalar, boshlang‘ich taqsimot va sinov ma’lumotlarini tozalash | `settings.manage` | ✅ | — | — |
| Django boshqaruv paneli (/admin/) | `admin_panel` | ✅ | — | — |

## Qanday ishlaydi

- **Funksiya view’lar:** `@role_required("day.approve")`. **Klass view’lar:** `RoleRequiredMixin` va `permission = "day.approve"`.
- Kirmagan foydalanuvchi login sahifasiga (`/kirish/`) yo‘naltiriladi, ruxsati yo‘q foydalanuvchi **403** sahifasini ko‘radi.
- Shablonlarda: `{% if can.day_approve %}…{% endif %}` (`naryad.context_processors.ui`). Menyu ham rolga qarab shu yerda tuziladi.
- **Boshqaruv paneli** (`/admin/`): faqat admin roli va superuser (`NaryadAdminSite.has_permission`). `is_staff` roldan avtomatik qo‘yiladi; admin roli barcha model huquqlariga ega.
- Hozir mavjud sahifalar: bosh sahifa, kirish, chiqish, parolni almashtirish, boshqaruv paneli; kursantlar bazasi (ro‘yxat, qo‘shish, tahrirlash, faolsizlantirish, Excel import) va kursant kartochkasi (6-bosqich). Kursant faqat o‘zining kartochkasini ko‘radi (`/mening-tarixim/`). Qolgan amallar keyingi bosqichlardagi sahifalar uchun oldindan belgilangan; ularning havolalari hozircha o‘chiq.

## Kirish xavfsizligi

| Qoida | Qiymat | Sozlama |
|---|---|---|
| Ketma-ket noto‘g‘ri urinishlar | 5 marta | `LOGIN_MAX_FAILURES` |
| Blok muddati | 15 daqiqa | `LOGIN_BLOCK_MINUTES` |
| Hisoblash kaliti | login (katta-kichik harfsiz) | `naryad/auth.py` |
| Birinchi kirishda parolni almashtirish | `User.must_change_password` | `create_cadet_accounts` avtomatik belgilaydi |

Blok platforma sahifasidagi va boshqaruv panelidagi kirishga birdek ishlaydi. Muvaffaqiyatli kirish hisobni tozalaydi; blokni admin panelda (*Login cheklovlari*) qo‘lda olib tashlash mumkin.
