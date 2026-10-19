# CLAUDE.md — E-NARYAD (2-kurs sutkalik naryad platformasi)

Bu fayl loyihaning yagona “manba hujjati”. Har bir javobdan oldin shu fayldagi qoidalarga amal qil. Qoidalar o‘zgarsa, avval shu fayl yangilanadi.

## 1. Loyiha haqida

- **Buyurtmachi:** Bojxona instituti (O‘zbekiston Respublikasi Iqtisodiyot va moliya vazirligi huzuridagi Bojxona qo‘mitasi), harbiylashtirilgan oliy ta’lim muassasasi.
- **Foydalanuvchi:** 2-kurs kursanti, loyiha muallifi.
- **Muammo:** sutkalik naryad qog‘ozda tuziladi. Har guruhdan bitta kursant ro‘yxat yozadi, bitta kursant umumiy ro‘yxatni shakllantiradi. Natijada adolatsizlik: kimdir bir haftada 2–3 marta, boshqalar 1 marta turadi; shaxsiy kelishmovchilik sababli bir kishi qayta-qayta bir joyga yuboriladi.
- **Maqsad:** faqat 2-kurs uchun sutkalik naryadni tarix asosida, adolatli va avtomatik tuzuvchi veb-platforma.

Kurslar naryadga haftama-hafta navbat bilan chiqadi (1-hafta 1-kurs, 2-hafta 2-kurs, ...). Platforma faqat 2-kurs haftalari uchun ishlaydi.

## 2. Kurs tarkibi

Jami 100 kursant: 87 o‘g‘il, 13 qiz. 6 guruh.

| Guruh | Jami | O‘g‘il | Qiz |
|---|---|---|---|
| YuP-125 (Yurisprudensiya) | 15 | 13 | 2 |
| BI-225 (Bojxona ishi) | 17 | 14 | 3 |
| BI-325 | 16 | 14 | 2 |
| BI-425 | 17 | 15 | 2 |
| BI-525 | 17 | 17 | 0 |
| BI-625 (rus tili) | 18 | 14 | 4 |

To‘liq ro‘yxat: `2-KURS ROYXATI.doc` (jins faylda yozilmagan; qizlar: Abduvaliyeva, Shamsiddinova, Abdullayeva, Karimova, Quvatova, Mamirova, Zoirova, Baxtiyorova, Panjiyeva, Azizova, Maxmudova, Muxammadiyeva, Ordabaeva).

**Naryaddan ozod (komandirlar va kurs lavozimlari)** — sutkalik naryadga umuman qo‘yilmaydi (10-bo‘lim, 56-band):

| Guruh | Kursant | Lavozimi |
|---|---|---|
| YuP-125 | Abduqodirov Abdulqosim Abdulxakim o‘g‘li | Kurs starshinasi |
| YuP-125 | Tojiyev Sherali Tolmas o‘g‘li | YuP-125 guruh komandiri |
| BI-225 | Eshmatov Jobirbek Baxtiyor o‘g‘li | BI-225 guruh komandiri |
| BI-225 | Bo‘riyev Shohruxmirzo Norbobo o‘g‘li | Kurs pisari |
| BI-325 | Akramjonov Axmadjon Akramjon o‘g‘li | BI-325 guruh komandiri |
| BI-325 | Xayrillayev Javohir Oybek o‘g‘li | Kaptyorchik |
| BI-425 | Navro‘zov Jasurbek Baxtiyor o‘g‘li | BI-425 guruh komandiri |
| BI-525 | Abdulazizov Oyatillo Abduxalilovich | BI-525 guruh komandiri |
| BI-625 | O‘rmonjonov Muxammadqodir Jaxongir o‘g‘li | BI-625 guruh komandiri |

**Naryadga chiqadigan o‘g‘il bolalar:** YuP-125 — 11, BI-225 — 12, BI-325 — 12, BI-425 — 14, BI-525 — 16, BI-625 — 13 (jami 78). Qizlar o‘zgarmaydi (13). Belgi `data/roster.json` da (`duty_exempt`, `duty_position`).

## 3. Navbatchilik joylari (1 sutka)

Har joydagi kishilar soni qat’iy, hech kim o‘zgartira olmaydi.

| № | Joy | Kim | Soni | Lavozimlar (tartibda) | PDF’dagi qator yozuvi |
|---|---|---|---|---|---|
| 1 | Markaz bo‘yicha | o‘g‘il | 1 | Navbatchi yordamchisi | Markaz bo‘yicha navbatchi yordamchisi |
| 2 | 1-NO‘J bo‘yicha | o‘g‘il | 4 | Navbatchi, Navbatchi yordamchisi, Posbon, Posbon | 1-NO‘J bo‘yicha navbatchi / navbatchi yordamchisi / posbon |
| 3 | 2-NO‘J bo‘yicha | o‘g‘il | 3 | Navbatchi, Posbon, Posbon | 2-NO‘J bo‘yicha navbatchi / posbon |
| 4 | 1-Yotoqxona bo‘yicha (1-sonli kursantlar yotoqxonasi) | o‘g‘il | 3 | Navbatchi, Posbon, Posbon | Kurs bo‘yicha navbatchi / posbon |
| 5 | O‘quv binosi bo‘yicha | o‘g‘il | 2 | Navbatchi, Posbon | O‘quv binosi bo‘yicha navbatchi / posbon |
| 6 | Institut bo‘yicha patrul | o‘g‘il | 4 | Posbon ×4 | Institut bo‘yicha patrul (faqat 1-qatorda) |
| 7 | Qizlar yotoqxonasi bo‘yicha (2-sonli) | qiz | 3 | Navbatchi, Posbon, Posbon | Qizlar yotoqxonasi bo‘yicha navbatchi / posbon |

Jami: 17 o‘g‘il + 3 qiz = 20 kishi (tasdiqlangan).

## 4. Taqsimlash qoidalari

### A. Guruhlar darajasi (o‘g‘il bolalar)

- Bir sutkada har bir joyning barcha o‘rinlari bitta guruhdan beriladi (masalan, 1-NO‘J ning 4 o‘rni hammasi BI-525 dan).
- 6 guruh, 6 ta o‘g‘il bolalar joyi: har sutka har guruh aynan bitta joy beradi.
- Guruhlar joylar bo‘yicha navbatma-navbat aylanadi: bugun 1-NO‘J ni o‘tagan guruh ertaga boshqa joyga o‘tadi, 1-NO‘J ga navbati kelgan keyingi guruh chiqadi.
- Bir guruh ketma-ket ikki sutka bir xil joyga tushmaydi.
- **Aylanish (tasdiqlangan):** Markaz → 1-NO‘J → 2-NO‘J → 1-Yotoqxona → O‘quv binosi → Patrul → Markaz (har guruh har sutka zanjirda keyingi joyga o‘tadi). Keyingi 2-kurs haftasi oldingi haftaning oxirgi sutkasidan davom etadi.

### B. Kursantlar darajasi (guruh ichida)

- Har bir kursantning naryad tarixi saqlanadi: qachon, qaysi joyda, qaysi lavozimda.
- Guruhga joy tushganda guruh ichidan tarix bo‘yicha tanlanadi: eng kam naryad o‘tagan va shu joyda/lavozimda eng kam turgan birinchi.
- Bir hafta ichida guruhdagi hamma kursant kamida bir marta turmaguncha hech kim ikkinchi marta tushmaydi.
- Hamma bir martadan turib bo‘lgach: kim qaysi joyga kamroq tushgan bo‘lsa, o‘sha joyga o‘sha qo‘yiladi. Bir kursant qayta-qayta bitta joyga tushmasligi kerak.
- Adolat hisobi har bir guruh kesimida yuritiladi (87 kishi bo‘yicha emas), chunki guruhlarda o‘g‘il bolalar soni har xil.
- **Naryaddan ozod kursantlar** (komandirlar va kurs lavozimlari, 2-bo‘lim) nomzodlar hovuziga umuman kirmaydi: generator ularni tanlamaydi, qo‘lda ham qo‘yib bo‘lmaydi, qoralamada bo‘lsa — qizil ogohlantirish va tasdiqlab bo‘lmaydi. Ozod kursant faol qoladi (akkaunti ishlaydi). Adolat (min/max/o‘rtacha, ±1 ulushi) va “bir o‘g‘ilga o‘rtacha naryad” faqat naryadga chiqadiganlar bo‘yicha hisoblanadi; ozodning o‘tmishdagi naryadlari tarixda qoladi. Algoritm qoidalari o‘zgarmaydi.

### C. Qizlar

- Qizlar faqat Qizlar yotoqxonasiga chiqadi.
- Guruhga bog‘lanmaydi: 13 qiz bitta umumiy navbat, faqat shaxsiy tarix bo‘yicha (turli guruhlardan aralash bo‘lishi mumkin).
- Navbatchi va posbon lavozimlari ham tarix bo‘yicha almashib turadi.

### D. Tavsiya etilgan saralash kaliti (guruh ichida)

1. Shu haftada necha marta turgan (kam oldin, qat’iy).
2. Jami naryadlar soni (+1 jarima, agar oxirgi naryadi ham shu joy bo‘lsa).
3. Oxirgi naryadi shu joy bo‘lganlar orqaga.
4. Shu joyda necha marta turgan.
5. Oxirgi naryad sanasi (uzoq dam olgan oldin).
6. Teng bo‘lsa — sana+kursant asosidagi deterministik tasodif (alifbo tartibi emas).

**Lavozimlar:** tanlangan 2–4 kishiga barcha almashtirishlar ko‘rib chiqilib, har kim o‘sha lavozimda kam turgan va oxirgi lavozimi takrorlanmaydigan variant tanlanadi.

**Cheklovlar:** faol emas va sababli (kasal, ta’til) kursantlar olinmaydi; kecha naryadda bo‘lgan olinmaydi — boshqa odam qolmasa ham olinmaydi: o‘rin bo‘sh qoladi, ogohlantirish chiqadi va o‘rinni admin qo‘lda to‘ldiradi (10-bo‘lim, 13-band).

## 5. Rasmiy shakl (PDF, A4, Times New Roman)

```
                                   Bojxona instituti Navbatchilik
                                   qismi boshlig‘i, podpolkovnik
                                   X.Sattorovga

   2026-yil 18-sentabr kunidan 19-sentabr kuniga sutkalik naryadlar ro‘yxati
                          2-kurs ro‘yxati

| Lavozim                                | F.I.Sh.        | Guruh   |
| Markaz bo‘yicha navbatchi yordamchisi  | G‘ayratov G‘   | BI-625  |
| **1-NO‘J bo‘yicha**  (bo‘lim sarlavhasi)                          |
| 1-NO‘J bo‘yicha navbatchi              | Sa’dullayev B  | BI-525  |
| ... 7 bo‘lim, tartib: Markaz, 1-NO‘J, 2-NO‘J, 1-Yotoqxona,
|     O‘quv binosi, Institut bo‘yicha patrul, Qizlar yotoqxonasi |

Kurs boshlig‘i                                        X.Turobov
mayor
```

- F.I.Sh. qisqa shaklda: Familiya + ism bosh harfi. Ikki harfli tovushlar saqlanadi: Shavkatov Sh, G‘ayratov G‘, Mexmonov Sh.
- Sarlavha, qabul qiluvchi va imzo (ism, unvon) sozlamalardan olinadi, kodga yozilmaydi.

## 6. Platforma funksiyalari

- **Kursantlar bazasi:** F.I.Sh., guruh, jinsi; qo‘shish, tahrirlash, faolsizlantirish (tarix o‘chmasligi uchun), Excel’dan import.
- **Naryad generatori:** sana → avtomatik qoralama → ko‘rib chiqish → tasdiqlash. Faqat tasdiqlangan sutkalar tarixga kiradi.
- **Qo‘lda tuzatish** (kasallik, ta’til, sababli holat): sabab majburiy, jurnalga yoziladi (kim, qachon, kimni kimga almashtirdi).
- **Tarix va statistika:** har kursant/guruh bo‘yicha qayerda, necha marta, qaysi lavozimda; adolat ko‘rsatkichi (guruh ichida min/max farqi).
- **PDF eksport va chop etish.**
- **Rollar:** admin (kurs boshlig‘i) — hammasi: hafta ochish, qoralamani tuzish (ro‘yxatni dastur avtomatik tuzadi), tuzatish, tasdiqlash; kursant — faqat ko‘rish. Alohida “tuzuvchi” roli yo‘q (10-bo‘lim, 26-band).
- Interfeys o‘zbek tilida (lotin), mobil qurilmalarga mos.

## 7. Texnologiyalar steki (kelishilgan)

- Python 3.12, Django 5, PostgreSQL (ishlab chiqishda SQLite)
- Django shablonlari + HTMX + Tailwind CSS
- PDF: WeasyPrint; Excel: openpyxl
- Algoritm frameworkdan mustaqil toza Python modulida (`naryad/engine/allocator.py`), pytest bilan testlanadi
- Docker + docker-compose
- Joylashtirish (deploy): Railway (Dockerfile orqali, Railway PostgreSQL bazasi; sozlamalar muhit o‘zgaruvchilaridan: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`)

## 8. Ma’lumotlar bazasi (asosiy jadvallar)

`group`, `cadet`, `post`, `post_slot`, `duty_week`, `duty_day` (status: draft/approved), `group_post_assignment`, `assignment` (unique: sutka+o‘rin, sutka+kursant), `absence`, `change_log`, `user` (+role), `setting`. Statistika alohida saqlanmaydi, `assignment` dan hisoblanadi.

Javoblar o‘zbek tilida, lotin yozuvida. Kod ichidagi nomlar inglizcha, izohlar va interfeys matnlari o‘zbekcha.

## 9. Ish tartibi (Claude uchun)

- Har safar faqat joriy bosqichni bajar. Keyingi bosqichga o‘tma.
- Tushunarsiz joy bo‘lsa, taxmin qilmasdan avval so‘ra. Savollar raqamlangan, har biriga o‘z tavsiyangni yoz.
- Kod to‘liq, ishlaydigan, fayl yo‘li bilan beriladi (`naryad/models.py` va h.k.). “...qolgani avvalgidek” deb qisqartirma.
- Har bosqich oxirida: nima qilindi, qanday ishga tushiriladi/tekshiriladi (buyruqlar), qaysi savollar ochiq qoldi.
- Qoidalarni (4-bo‘lim) buzadigan har qanday o‘zgarish oldidan ogohlantir.

## 10. Qabul qilingan qarorlar (1-bosqich, tasdiqlangan)

1. **Vaqt:** sutka — 18:00 dan ertasi 18:00 gacha, boshlangan sanasi bilan nomlanadi. 2-kurs haftasi — yakshanba 18:00 dan keyingi yakshanba 18:00 gacha (7 sutka). Kurslar haftama-hafta navbat bilan chiqadi; interval kodga qotirilmaydi — keyingi hafta sanasi sozlamadagi `week_interval_days` bo‘yicha taklif qilinadi, admin tasdiqlaydi.
2. **Ismlar:** rasmiy ro‘yxat (`2-KURS ROYXATI.doc`) asosiy manba (Mexmonov Sh, Yuldoshov M, Maxmudova H). Kerak bo‘lsa, kursantga qisqa shakl qo‘lda beriladi.
3. **Belgilar** (6-bosqichda yangilandi): import va tahrirda `o‘`, `g‘` uchun `‘` (U+2018), tutuq belgisi uchun `’` (U+2019) ishlatiladi (oldin ʻ U+02BB / ʼ U+02BC edi; bazadagi yozuvlar migratsiya bilan o‘tkazildi). Qoraqalpoqcha harflar (`ǵ`, `í`, `á`) o‘zgarmaydi.
4. **Tasdiqlangan sutka:** faqat admin sabab ko‘rsatib qayta ochadi, tuzatadi va qayta tasdiqlaydi; hammasi jurnalga yoziladi.
5. **Qoralama:** sutkama-sutka tuziladi. Bir haftalik qoralama birdan tuzilmaydi; keyingi sutka faqat oldingisi tasdiqlangach tuziladi.
6. **Birinchi sutka:** guruh→joy taqsimotini admin qo‘lda kiritadi, keyin zanjir avtomatik davom etadi.
7. **Oldingi tarix:** admin o‘tgan (qog‘ozdagi) sutkalarni qo‘lda tasdiqlangan sutka sifatida kirita oladi.
8. **PDF shrifti:** Times New Roman (serverga o‘rnatiladi).
9. **Kursantlar:** har biriga login; admin hisoblarni ommaviy yaratadi, parol birinchi kirishda almashtiriladi.
10. **Sababli yo‘qlik:** sutka sanalari bo‘yicha, boshlanish va tugash sanasi ham ichida.
11. **Qizlar:** “hamma bir marta turmaguncha hech kim ikkinchi marta tushmaydi” qoidasi 13 qizning umumiy navbati uchun ham qat’iy.
12. **Jadval nomlari:** `group` → `study_group`, `user` → `app_user` (SQL zahiralangan so‘zlar va Django modellari bilan to‘qnashuv sababli). To‘liq sxema: `docs/01-talablar-va-sxema.md`.
13. **Kecha naryadda bo‘lgan kursant** (2-bosqich): hech qachon avtomatik olinmaydi. Nomzod yetmasa, o‘rin (oxirgi posbon o‘rinlaridan boshlab) bo‘sh qoldiriladi, qoralamaga ogohlantirish yoziladi va o‘rinni admin qo‘lda to‘ldiradi.
14. **Sutka faqat ochilgan hafta ichida** (3-bosqich; 4-bosqichda aniqlashtirildi): 2-kurs haftasini (`DutyWeek`) faqat admin ochadi (yoki `import_history` o‘tgan sutka uchun yaratadi); sutka qoralamasi faqat shu hafta ichidagi sanaga tuziladi. Hafta ichida sutkalar oraliq qoldirmay ketma-ket tuziladi: bazadagi oxirgi sutkadan keyingi kun. Platformagacha bo‘lgan (bazada yozuvi yo‘q) sutkalar to‘siq emas — masalan, faqat 18-sentabr import qilingan bo‘lsa, 19-sentabr tuziladi.
15. **Bir joyga takror tushish** (2-bosqich kuzatuvi): hozircha saralash kaliti o‘zgarmaydi, statistika bosqichida haqiqiy ma’lumotda kuzatiladi.
16. **Ro‘yxatdagi g‘alati yozuvlar** (`Po‘Lotovich`, `Bahodir Xon`) o‘zgartirilmaydi; kerak bo‘lsa admin interfeysda tuzatadi.
17. **Admin panel tarjimasi** (3-bosqich): Django’ning o‘zbekcha admin tarjimasidagi yetishmagan matnlarni interfeys bosqichida o‘zimiz tarjima qilamiz (`locale/uz`).
18. **O‘tgan tarixni import qilish** (4-bosqichda bajarildi): `python manage.py import_history <fayl.xlsx|.csv> [--dry-run]`. Sutkalar `approved`, `Assignment.source = manual`, jurnalga “qog‘ozdan import”. Ism taxmin qilinmaydi: topilmagan yoki bir nechta mos kelgan ism — xato, hech narsa yozilmaydi.
19. **Rollar va kirish:** Django admin panelga faqat admin roli va superuser kiradi (`NaryadAdminSite.has_permission`; `is_staff` roldan avtomatik). Admin roli barcha huquqlarga ega. Kursant o‘z sahifalari (platforma interfeysi) orqali ishlaydi.
20. **Boshlang‘ich taqsimot** (4-bosqich): bazada tasdiqlangan tarix bo‘lmasa, birinchi sutkaning guruh → joy taqsimotini admin Sozlamalar sahifasida kiritadi (6 guruh × 6 joy, har biri bir marta). Usiz generator o‘zbekcha xato bilan to‘xtaydi.
21. **Importda ketma-ket ikki sutka turgan kursant** (5-bosqich): import to‘xtatilmaydi, faqat qator raqami bilan ogohlantirish chiqadi (qog‘ozdagi haqiqiy ma’lumot).
22. **load_roster** faqat birinchi ishga tushirishda ishlatiladi; keyin kursantlar admin panelda tahrirlanadi (qayta ishlatilsa admin tuzatishlarini roster.json holatiga qaytaradi).
23. **Joy nomlari (import)**: hozirgi variantlar qoladi (kod, nomi, “Kurs bo‘yicha”, “Patrul” va h.k.); yangilari chiqsa keyin qo‘shiladi.
24. **Rollar va ruxsatlar** (5-bosqich): yagona jadval `naryad/permissions.py` (`docs/05-rollar.md`). Sababli yo‘qliklarni kiritish — admin.
25. **Kirish xavfsizligi** (5-bosqich): 5 marta noto‘g‘ri urinish → login 15 daqiqaga bloklanadi; kursant akkauntlari vaqtinchalik parol bilan yaratiladi va birinchi kirishda parol majburiy almashtiriladi.
26. **Tuzuvchi roli olib tashlandi** (5-bosqichdan keyin): ro‘yxatni dastur o‘zi tuzadi, shuning uchun alohida “tuzuvchi (navbatchi kursant)” roli kerak emas. Faqat ikki rol (19-bosqichdan uchta — 67-band): **admin** (kurs boshlig‘i) — hafta ochish, qoralama tuzish tugmasi, sabab bilan tuzatish, tasdiqlash, hammasi; **kursant** — faqat tasdiqlangan sutkalar va o‘z tarixi. Bazadagi eski `compiler` rolidagi foydalanuvchilar migratsiyada `cadet` ga o‘tkaziladi.
27. **PDF’ni kursantlar ham yuklab oladi** (5-bosqichdan keyin; 14-bosqichda bekor qilingan edi, **16-bosqichda qayta tiklandi — 63-band**): tasdiqlangan sutkaning PDF’ini har bir kursant yuklab olishi va chop etishi mumkin; qoralama PDF’i — faqat admin.
28. **Kursantlar ro‘yxati** (6-bosqich): faqat admin ko‘radi va boshqaradi (tuzuvchi roli yo‘q — 26-band); kursant faqat o‘z kartochkasini ko‘radi (`/mening-tarixim/`). Qidiruv — familiya bo‘yicha.
29. **Faolsizlantirish** (6-bosqich): sabab majburiy (chetlatilgan, akademik ta’til, boshqa kursga o‘tgan, boshqa — izoh bilan); kursantning akkaunti ham bloklanadi, qayta faollashtirilganda tiklanadi. Hammasi jurnalga yoziladi.
30. **Guruh yoki jins o‘zgarishi** (6-bosqich): naryad tarixi bor kursantda tasdiqlash belgisi talab qilinadi; tarix o‘chmaydi (eski naryadlar o‘sha paytdagi guruh bilan qoladi), jurnalga yoziladi. Boshqa guruhga o‘tgan kursant yangi guruh ro‘yxatining oxiriga tushadi.
31. **Jurnal** (6-bosqich): `ChangeLog` endi kursantlar bazasidagi o‘zgarishlarni ham yozadi (qo‘shish, tahrirlash, faolsizlantirish, qayta faollashtirish, Excel import) — `cadet` + `details` maydonlari bilan.
32. **Qoralamada faol emas / sababli yo‘q kursant** (6-bosqich savoli, 7-bosqichda bajarildi): sutka sahifasida qizil ogohlantirish chiqadi va bunday qoralamani tasdiqlab bo‘lmaydi — qo‘lda almashtirish yoki “Qayta tuzish” kerak. Faolsizlantirilgan kursantning akkaunti ham bloklanadi (29-band o‘z kuchida).
33. **Sutka oqimi** (7-bosqich): admin haftani ochadi (faqat yakshanba) → “Tuzish” (qoralama) → qo‘lda tuzatish (sabab majburiy: kasal / ta’til / sababli / boshqa + izoh) → tasdiqlash. Bo‘sh o‘rin, faol emas yoki sababli yo‘q kursant bo‘lsa tasdiqlanmaydi. “Qayta tuzish” avvalgi qoralamani almashtiradi va jurnalga yoziladi.
34. **Qo‘lda almashtirish qoidalari** (7-bosqich): boshqa guruhdan, qizni o‘g‘il o‘rniga (va aksincha), kecha naryadda bo‘lgan, shu sutkada boshqa o‘rinda turgan, faol emas yoki sababli yo‘q kursantni qo‘yib bo‘lmaydi. Nomzodlar algoritm kaliti (`pick_cadets`) bo‘yicha saralanadi. Sabab “kasal” yoki “ta’til” bo‘lsa, almashtirilgan kursantga shu sutka uchun sababli holat avtomatik yoziladi. Lavozimlarni o‘zaro almashtirish — faqat bitta joy ichida.
35. **Tasdiqni bekor qilish** (7-bosqich): faqat admin, sabab majburiy, faqat keyingi sutka hali tuzilmagan bo‘lsa.
36. **Sababli holat turlari** (7-bosqich): kasal / ta’til / sababli / boshqa (oldingi “xizmat safari” — sababli). Boshlangan (tarixi bor) yozuv o‘chirilmaydi, faqat tugash sanasi o‘zgartiriladi; kelgusidagisini o‘chirish mumkin. Bir kursantga ustma-ust yozuv kiritilmaydi. Hammasi jurnalga yoziladi.
37. **Bir vaqtda ishlash** (7-bosqich): har sutkada `version`; har o‘zgartirish `select_for_update` bilan qulflaydi va versiyani tekshiradi — mos kelmasa “sahifani yangilang” xabari chiqadi.
38. **Qoralamani o‘chirish** (8-bosqich): faqat admin, faqat eng oxirgi qoralama, sabab majburiy, jurnalga yoziladi (jurnal `day_date` orqali saqlanib qoladi). Shu yo‘l bilan oldingi sutkaning tasdig‘ini bekor qilish mumkin bo‘ladi.
39. **Bo‘sh o‘ringa kursant qo‘yish** — sabab majburiy (o‘zgarmaydi). **“Qayta tuzish”** — ogohlantiruvchi tasdiqlash oynasi bilan (o‘zgarmaydi).
40. **PDF** (8-bosqich): rasmiy shakl, A4, bitta sahifa, WeasyPrint. Shrift: `fonts/times.ttf` (+ `timesbd.ttf`) bo‘lsa — Times New Roman, bo‘lmasa — Liberation Serif (o‘lchamlari bir xil). Times New Roman fayllari repozitoriyda yo‘q (`.gitignore`). Jadvalda “Lavozim | F.I.Sh. | Guruh” sarlavha qatori bor, Markazdan tashqari har bo‘lim qalin sarlavha qatori bilan boshlanadi. Qoralama PDF’ida har sahifada xira “QORALAMA” yozuvi.
41. **PDF ruxsatlari va fayl nomlari** (8-bosqich; 14-bosqichda PDF faqat admin bo‘lgan edi, 16-bosqichda qayta tiklandi — 63-band): tasdiqlangan sutka PDF’i — hamma rol; qoralama PDF’i — faqat admin; hafta PDF’ida kursant faqat tasdiqlangan sutkalarni oladi. Nomlar: `naryad_2026-09-18.pdf`, `naryad_hafta_2026-09-13.pdf`.
42. **Markaz qatori** (8-bosqich savoli): bitta qator — “Markaz bo‘yicha navbatchi yordamchisi”, 1 o‘rin. Namunadagi ikkinchi qator xato.
43. **Imzo joylashuvi**: chapda “Kurs boshlig‘i”, ostida unvon (“mayor”), o‘ngda “X.Turobov” — hozirgi holat qoladi.
44. **Telefondan chop etish**: chop etish sahifasidagi “PDF’ni alohida ochish” havolasi bilan — hozirgi holat qoladi.

45. **Statistika** (9-bosqich): faqat tasdiqlangan sutkalar, so‘rov paytida `Assignment` dan hisoblanadi (alohida jadval yo‘q). Davr: butun tarix / sanadan sanagacha / bitta 2-kurs haftasi. “Shu haftada” — tanlangan hafta, bo‘lmasa boshlangan eng oxirgi 2-kurs haftasi. Sahifa va Excel — faqat admin (`history.all`).
46. **Adolat belgisi**: har guruh o‘g‘illari va qizlar alohida, faqat faol kursantlar, jami naryadlar bo‘yicha farq (max − min): yashil ≤ 1, sariq = 2, qizil ≥ 3. “Ketma-ket bir joy” — kursantning o‘z tasdiqlangan naryadlari ketma-ketligida ikki qo‘shni naryadi bir joyda; qizlarda joy bitta bo‘lgani uchun tekshirilmaydi.
47. **Qo‘lda tuzatishlar nazorati**: faqat hozir tasdiqlangan sutkalardagi almashtirishlar va sutka oxirgi marta (qayta) tuzilgandan keyingilari sanaladi. Sabab turi `ChangeLog.reason_code` da saqlanadi (eski yozuvlar migratsiyada matndan to‘ldirildi). Ogohlantirish qoidasi: qo‘lda qo‘yilish kamida 2 marta **va** hovuz (guruh o‘g‘illari yoki qizlar) o‘rtachasidan kamida 2 baravar ko‘p.
48. **Kursant kartochkasi**: o‘z naryadlari soni va hovuzi (guruh o‘g‘illari yoki qizlar) o‘rtachasi, butun tarix bo‘yicha; boshqa kursantlarning ismlari ko‘rsatilmaydi.
49. **Simulyatsiya** (`scripts/simulate_weeks.py`): faqat alohida, bo‘sh bazada ishlaydi (sutka bor bo‘lsa to‘xtaydi); platformaning o‘z oqimi bilan 12 hafta (har 14 kunda) tuzadi, tasodifiy va ataylab qo‘lda almashtirishlar qo‘shadi.
50. **10-bosqich qarorlari (9-bosqich savollari):** tuzuvchi roli qaytarilmaydi — sutkani tuzish, tuzatish va tasdiqlashni faqat admin qiladi; rollar: admin va kursant. Qo‘lda qo‘yish ogohlantirishi chegarasi (≥ 2 marta va hovuz o‘rtachasidan ≥ 2 baravar) va adolat belgisi chegaralari (yashil ≤ 1, sariq = 2, qizil ≥ 3) o‘zgarmaydi. Qizlar uchun statistikaga “ketma-ket ikki naryadda ham navbatchi bo‘lgan” holatlar soni qo‘shildi (kartochka, ro‘yxat, Excel). Kursant kartochkasidagi solishtirish butun tarix bo‘yicha qoladi.
51. **Production** (10-bosqich): `config/settings_prod.py` — `DEBUG=False` majburiy, maxfiy kalit ≥ 50 belgi, HTTPS’ga yo‘naltirish, `Secure`/`HttpOnly` cookie (`__Secure-` nomli), HSTS 1 yil, `X-Frame-Options: DENY` (faqat PDF javobi `SAMEORIGIN` — chop etish iframe’i uchun), Content-Security-Policy `script-src 'self'` (inline JavaScript yo‘q, hammasi `static/js/` da). `check --deploy` — 0 ogohlantirish.
52. **Server tarkibi**: `docker-compose.prod.yml` — web (gunicorn), PostgreSQL 16, Caddy (domen `.env` dan, avtomatik HTTPS; `DOMAIN=:80` + `DJANGO_HTTPS=False` — internetsiz ichki tarmoq), backup (har kuni 03:00, `pg_dump` custom format, 30 kun). Statik fayllar — WhiteNoise. `/health/` — Host va HTTPS tekshiruvidan oldin ishlaydigan middleware (konteyner healthcheck’i uchun). Loglar: konsol + fayl (5 MB × 5), Docker loglari 10 MB × 5.
53. **Excel yuklash cheklovlari**: faqat `.xlsx`, ≤ 2 MB, haqiqiy ZIP/Excel tuzilmasi, ochilgandagi hajm ≤ 30 MB, ≤ 1000 qator, ≤ 30 ustun.
54. **Interfeys**: barmoq bilan bosiladigan elementlar kamida 44 px (`static/src/input.css`), matn kesilmaydi (truncate yo‘q), 360 px’da gorizontal toshish yo‘q (`scripts/ui_audit.py`). 403/404/500 sahifalari o‘zbekcha. Django’ning “Guruhlar (huquqlar)” bo‘limi admin paneldan olib tashlandi (rollar `User.role` da). Admin tarjimalaridagi apostroflar ‘/’ standartiga keltirildi.
55. **Versiya 1.0.0** (10-bosqich yakuni): `CHANGELOG.md`, git tag `v1.0.0`.
56. **Naryaddan ozod kursantlar** (qo‘shimcha o‘zgarish, 1.0.0 dan keyin): 9 kursant — kurs starshinasi, kurs pisari, kaptyorchik va 6 guruh komandiri — sutkalik naryadga qo‘yilmaydi (ro‘yxat 2-bo‘limda). `Cadet.duty_exempt` + `duty_position` (`is_active` dan alohida). Migratsiya 0010 ularni guruh + to‘liq F.I.Sh. bo‘yicha aniq topadi: topilmasa yoki bir nechta mos kelsa, xato bilan to‘xtaydi (bo‘sh bazada hech narsa qilmaydi — belgini `load_roster` roster.json dan qo‘yadi). Admin kursant kartochkasidan belgini qo‘yadi/olib tashlaydi (lavozim va sabab majburiy, jurnalga yoziladi); Django admin panelida bu maydonlar faqat o‘qish uchun. Lavozimdan bo‘shagan kursant qayta naryadga qo‘shiladi va algoritm uni haftalik/jami hisob bo‘yicha avtomatik oldinga qo‘yadi (kutilgan xatti-harakat, `docs/02-algoritm.md` 4-bo‘lim).
57. **Naryaddan ozodlar bo‘yicha qarorlar (1.1.0 ochiq savollari, tasdiqlangan):**
    - Ozoddan qaytgan kursant uchun hisob tenglashtirilmaydi. Algoritm uni haftalik va jami hisob bo‘yicha o‘zi oldinga qo‘yadi (haftasiga ko‘pi bilan bitta ortiqcha naryad), u bir necha haftada guruhga yetib oladi.
    - `load_roster` qayta ishga tushirilsa, ozodlar ro‘yxati `roster.json` holatiga qaytadi va jurnalga yoziladi. Buyruq faqat birinchi o‘rnatishda ishlatiladi.
    - Yangi lavozimga tayinlanganni admin kartochkadan belgilaydi. U ochiq qoralamada bo‘lsa, ogohlantirish chiqadi va admin uni almashtiradi.
58. **Dizayn (12-bosqich, 1.3.0):** asosiy rang — **to‘q ko‘k** (`brand`, foydalanuvchi qarori: prompt’dagi “yashil qoladi” o‘rniga), aksent — emblemadagi oltin (`gold`); holat ranglari (tasdiqlangan, adolat yashil/sariq/qizil) o‘zgarmaydi. Sarlavhada Davlat bojxona xizmati emblemasi, kirish va bosh sahifada institut binosi rasmi (asl fayllar `assets/`, tayyorlash `scripts/prepare_images.py`). Bosh sahifada jonli soat (server vaqti asosida, Toshkent UTC+5), joriy sutka paneli va har 60 soniyada HTMX yangilanish. Tungi rejim: kunduzgi / tungi / avtomatik, `localStorage`. CSP, algoritm, qoidalar, PDF va admin panel o‘zgarmaydi.
59. **Uch til (13-bosqich, 1.4.0):** o‘zbekcha (asosiy, lotin), ruscha, inglizcha.
    - **Tanlash:** sukut bo‘yicha doim o‘zbekcha; brauzerning `Accept-Language` sarlavhasi hisobga olinmaydi.
    - **Saqlash:** tanlov kirgan foydalanuvchida `User.language` da saqlanadi (boshqa qurilmada ham shu til), kirmaganda `naryad_til` cookie’sida. Kirishda cookie’dagi til foydalanuvchiga o‘tadi, agar u hali til tanlamagan bo‘lsa.
    - **Manzil va o‘tkazgich:** URL’da til prefiksi yo‘q. O‘tkazgich `UZ | RU | EN` sarlavhada (tungi rejim tugmasi yonida) va kirish sahifasida joylashgan; POST + CSRF bilan ishlaydi va o‘sha sahifaga qaytaradi. Kod: `naryad/i18n.py` (`LanguageMiddleware`, `set_language`).
    - **Tarjima qilinadi:** shablonlar, model nomlari va tanlovlar, formalar, xabarlar, ogohlantirishlar, menyu, statistika sarlavhalari, 403/404/500, admin panel.
    - **Bazadagi doimiy nomlar** (joylar, PDF qatorlari, yo‘nalishlar) `naryad/i18n_data.py` da ro‘yxatlangan va ko‘rsatishda tarjima qilinadi.
    - **msgid:** hozirgi o‘zbekcha matn.
    - **Sanalar:** “14-oktabr 2026” / “14 октября 2026” / “14 October 2026” (`i18n.long_date`).
    - **JavaScript matnlari:** serverdan `data-` atributlari orqali keladi, CSP o‘zgarmaydi.
    - **Tarjima qilinmaydi:** PDF naryad shakli (`translation.override("uz")`), Excel eksport, kursant F.I.Sh., guruh kodlari, admin yozgan sabab/izohlar, jurnalda saqlangan matnlar. Jurnal va sabablar har doim o‘zbekcha saqlanadi.
    - **Atamalar** `docs/atamalar.md` bo‘yicha; yangi matn shu lug‘atga mos tarjima qilinadi.
    - **Katalog yangilash:** `manage.py makemessages -l ru -l en --no-obsolete --no-location -i "tests/*" -i "scripts/*" -i "naryad/engine/*" -i "naryad/migrations/*" -i "docs/*" -i "staticfiles/*" -i "assets/*" -i "templates/naryad/pdf/*"`. Loyihaning `makemessages` buyrug‘i `_lazy` taxallusini ham taniydi.
    - **Kompilyatsiya:** `python scripts/compile_messages.py`.
    - **Test:** `tests/test_i18n.py` bo‘sh/fuzzy yozuv va qolib ketgan o‘zbekcha so‘zlarni tekshiradi.
60. **Kursant ko‘rinishi va ertangi ro‘yxat muddati (14-bosqich, 1.5.0):**
    - **~~Kursant faqat o‘z naryadini ko‘radi.~~** (16-bosqichda BEKOR QILINDI — 63-band; kartochka saqlanadi.) Bosh sahifadagi “Mening navbatdagi naryadim” kartochkasida:
      - sana va vaqt: “15-oktabr, chorshanba 18:00 → 16-oktabr 18:00”;
      - joy, lavozim va guruh;
      - jonli hisoblagich: “Naryadga … qoldi”, naryad davomida “Hozir naryaddasiz, smena almashishiga … qoldi”. Matnlar server vaqtidan, JS shablonlari `data-` atributlarida;
      - tayyorgarlik eslatmasi.

      Naryad bo‘lmasa: “Yaqin kunlarda tasdiqlangan naryadingiz yo‘q”. Kartochka ostida faqat “shu haftada / jami” va “Mening tarixim” havolasi.
    - **Ko‘rinish chegarasi** (16-bosqichda BEKOR QILINDI — 63-band; endi kursant tasdiqlangan sutka sahifasi va PDF’ini ko‘radi): faqat tasdiqlangan sutkalar ko‘rinadi, qoralama hech qachon. `day.view_approved` va `pdf.export` — faqat admin edi. Kursantga 403 qaytadi:
      - sutka sahifalari;
      - “Tasdiqlangan naryadlar” ro‘yxati (menyudan olib tashlandi);
      - PDF va chop etish;
      - boshqa kursantlarning kartochkalari.

      Bu 27- va 41-bandlardagi kursant PDF ruxsatini bekor qiladi.
    - **“Naryadingiz bekor qilindi”:** sutka tasdiqlanganda uning kursantlari `PublishedDuty` ga yoziladi. Tasdiq bekor qilinib kursant ro‘yxatdan chiqarilsa (almashtirilsa yoki qoralama o‘chirilsa), sutka tugaguncha unga sababsiz shu xabar chiqadi. Tasdiq bekor qilingan, lekin kursant hali qoralamada bo‘lsa, xabar yo‘q va naryad ko‘rinmaydi.
    - **Tayyorgarlik eslatmasi:** `PrepNote` — har joy uchun uch tilda, Sozlamalar sahifasida. Joriy tildagisi bo‘sh bo‘lsa o‘zbekchasi ko‘rsatiladi, hammasi bo‘sh bo‘lsa — hech narsa.
    - **Muddat:** D sanadagi sutka D kuni 18:00 dan `Setting.approval_lead_hours` soat oldin (standart 24 — D−1 kuni 18:00) tasdiqlangan bo‘lishi kerak. Admin bosh sahifasida ertangi sutka uchun banner (`naryad/readiness.py`):
      - sariq — muddat hali o‘tmagan, qolgan vaqt bilan, “Tuzish”/“Ochish” tugmasi;
      - qizil — “Muddat o‘tdi, kursantlar hali bilmaydi”;
      - yashil — tasdiqlangan.

      Bugun 18:00 da boshlanadigan sutka hali tasdiqlanmagan bo‘lsa, birinchi u uchun qizil banner chiqadi. Banner faqat 2-kurs haftasiga kiradigan sutka uchun ko‘rinadi, hafta boshlanishidan oldingi shanba ham shunga kiradi. Sutkalar ketma-ketligi qoidasi o‘zgarmaydi.
61. **Zalyotchiklar — navbatdan tashqari jazo naryadi (15-bosqich, 1.6.0):**
    - **Kim zalyotchik:** ichki tartib-qoidalarni buzgan yoki naryadda uxlab qolib tanbeh olgan kursant.
      - Admin “Zalyotchiklar” sahifasida kiritadi: kursant, sabab turi (Ichki tartib-qoidalarni buzish / Naryadda uxlab qolish / Boshqa), izoh (majburiy), buyruq/tanbeh sanasi, 1–10 ta jazo naryadi.
      - Bir kursantda bitta faol zalyot bo‘ladi; yangisi kiritilsa, soni mavjudiga qo‘shiladi va jurnalga alohida yozuv tushadi.
      - Holat: faol → (hammasi o‘tilgach avtomatik) bajarildi. Admin sabab yozib bekor qilishi mumkin.
      - Har amal ChangeLog’ga yoziladi: `penalty_add`, `penalty_cancel`, `penalty_done`, `penalty_resume`.
    - **Standart qoidalar** (o‘zgartirish mumkin):
      - faqat o‘g‘il kursant;
      - naryaddan ozod kursant bo‘lmaydi — avval ozodlik olib tashlanadi;
      - faolsiz kursant ham bo‘lmaydi.
    - **Naryadga qo‘yish (navbatdan tashqari):**
      - Faol zalyotchik guruhi qayerda turishidan qat’i nazar FAQAT 1-NO‘J yoki 1-Yotoqxonaga, POSBON o‘rniga qo‘yiladi (posbon o‘rinlari oxiridan). Shu joy guruhi bitta kam beradi.
      - Bir sutkada bir joyga ko‘pi bilan `Setting.penalty_per_post` ta (standart 1, ko‘pi bilan 2), ya’ni sutkada 2 ta.
      - Navbat: tanbeh sanasi eskisi; teng bo‘lsa — qolgan jazo naryadi ko‘prog‘i. Joy navbatma-navbat: o‘tgan safar 1-NO‘J bo‘lsa — endi 1-Yotoqxona (iloji bo‘lsa).
      - Qattiq cheklovlar o‘zgarmaydi: kecha turgan, sababli holatdagi, faolsiz kursant qo‘yilmaydi. Bunday holatda ogohlantirish chiqadi; o‘rin qolmasa, zalyotchik keyingi sutkaga qoladi.
    - **Oddiy navbat:** faol zalyotchik oddiy navbatda Markaz, 2-NO‘J, O‘quv binosi va Patrulga qo‘yilmaydi. Guruhi 1-NO‘J yoki 1-Yotoqxonaga tushgan kuni oddiy navbat bilan tura oladi — bu oddiy naryad, jazo hisobiga o‘tmaydi.
    - **Hisob:**
      - Jazo naryadi faqat sutka TASDIQLANGANDA “o‘tildi” sanaladi; tasdiq bekor qilinsa hisob qaytadi (bajarildi → yana faol).
      - `Assignment.kind` = normal / penalty, jazo naryadida `Assignment.penalty` bog‘lanadi.
      - Adolat hisobi faqat ODDIY naryadlarni sanaydi: statistika, nishonlar, saralash kaliti, guruhlar aylanishi, kursant kartochkasidagi sonlar. Jazo naryadi “kecha turgan” cheklovida hisobga olinadi.
    - **Dvigatel:** `naryad/engine/` Django’siz qoladi. `generate_day(offenders=…, penalty_per_post=…)`: jazo o‘rinlari oddiy to‘ldirishdan OLDIN belgilanadi (`place_offenders`). Zalyotchik bo‘lmasa, natija bayt-bayt avvalgidek — `tests/test_penalties.py` 84 sutkalik etalon xeshni tekshiradi.
    - **Qo‘lda tuzatish:**
      - jazo o‘rniga faqat boshqa faol zalyotchik (jazo naryadi bo‘lib qoladi) yoki shu joy guruhi kursanti (oddiy naryad) qo‘yiladi, sabab majburiy;
      - faol zalyotchikni boshqa joylarga qo‘lda qo‘yib bo‘lmaydi;
      - jazo o‘rnidagi zalyotchikning lavozimi almashtirilmaydi.
    - **Ko‘rinish:**
      - Sutka sahifasida jazo o‘rni “Zalyot” belgisi bilan chiqadi. PDF shakli O‘ZGARMAYDI — zalyotchik oddiy qator.
      - Kursant bosh sahifasida “Navbatdan tashqari naryad” va “Jazo naryadlari: 3 tadan 1 tasi o‘tildi”. Admin uchun kursant kartochkasida zalyot tarixi.
      - Statistika va Excel’da “Jazo naryadlari” ustuni, Excel’da “Zalyotchiklar” varag‘i.
62. **Zalyotchiklar bo‘yicha qarorlar (1.6.0 ochiq savollari, tasdiqlangan; 1.6.1):**
    - Kursant bosh sahifasidagi “Shu haftada / Jami” faqat oddiy naryadlarni sanaydi. Jazo naryadlari alohida: “Jazo naryadlari: 3 tadan 1 tasi o‘tildi”.
    - Faol zalyotchik oddiy navbatda boshqa joylarga qo‘yilmagani sabab oddiy naryadlari orqada qolsa, algoritm keyin uni tarix bo‘yicha o‘zi oldinga qo‘yadi. Alohida tenglashtirish yo‘q.
    - Faol zalyoti bor kursantni naryaddan ozod qilib bo‘lmaydi: avval zalyot bajarilishi yoki bekor qilinishi kerak (`cadets.exempt_blocker`).
    - Bekor qilingan zalyotning kursanti qoralamada jazo o‘rnida qolsa, sutka TASDIQLANMAYDI. Uni almashtirish yoki sutkani qayta tuzish kerak.
63. **Kursant tasdiqlangan ro‘yxatni ko‘radi, sababli holat eslatmasi, “ozod” yozuvi yo‘q (16-bosqich, 1.7.0):**
    - **Tasdiqlangan ro‘yxat:** `day.view_approved` va `pdf.export` — admin va kursant. Bu 60-banddagi “faqat o‘z naryadi” va “PDF faqat admin” qoidalarini bekor qiladi, 27- va 41-bandlar qayta kuchga kiradi.
      - Kursant menyusida “Tasdiqlangan naryadlar” bor. Sutka sahifasi faqat o‘qish uchun: joylar bo‘yicha guruhlangan, kursantning o‘z o‘rni ajratilgan (“Siz”). Bosh sahifadagi “Mening navbatdagi naryadim” saqlanadi.
      - PDF — rasmiy o‘zbekcha shakl, o‘zgarmagan.
      - Qoralama yoki tuzilmagan sutka (sahifa, PDF, chop etish) kursantga **403**. Qo‘shni sutka havolalari faqat tasdiqlanganlarga.
      - Kursantga ko‘rinmaydi (403 yoki shablonda chiqmaydi): tugmalar, sabablar, izohlar, jurnal, “qo‘lda” belgisi, boshqa kursantlarning kartochkasi va tarixi, statistika, sababli holatlar, zalyotchiklar.
      - Jazo naryadi ro‘yxatda oddiy posbon.
      - Ruxsatlar serverda tekshiriladi.
    - **Sababli holat eslatmasi:** `templates/partials/duty_reason_notice.html`, uch tilda. U kursant bosh sahifasida, “Tasdiqlangan naryadlar” va sutka sahifasida chiqadi; keyingi bosqichda guruh komandiri paneliga ham qo‘yiladi. Admin sahifalarida chiqmaydi.
    - **“Ozod” yozuvi olib tashlandi** (uch tilda). Ko‘rsatishda lavozim yozuvi (`duty_position`) qoladi; filtr va ustun — “Naryadga chiqmaydi” (`?holat=lavozimda`, eski `ozod` ham ishlaydi).
      - Faqat yozuv o‘zgardi: `duty_exempt`, generator qoidalari, adolat va o‘rtacha hisoblari (56-, 57-bandlar) o‘zgarmaydi.
      - Eski jurnal yozuvlari o‘zgarmaydi.
      - Atama `docs/atamalar.md` da. Testlar “ozod” so‘zini kursant ismlaridan (masalan, Ozodbek) ajratib tekshiradi (`tests/conftest.py::exempt_words`).
64. **Kasallar ro‘yxati (17-bosqich, 1.8.0):**
    - **Alohida jadval yo‘q.** Kasallik — `Absence` (`reason_type = "kasal"`) + `illness` (qisqa tavsif, faqat admin ko‘radi). Shuning uchun generator, almashtirish oynasi, “Sababli holatlar” sahifasi va zalyot ogohlantirishlari uni avtomatik hisobga oladi. Dvigatel o‘zgarmaydi. Xizmat: `naryad/sick.py`, sahifalar: `naryad/views_sick.py`, `/kasallar/`, ruxsat `sick.manage` (faqat admin, kursantga 403).
    - **Muddat:** sanalar sutka boshlanish sanalari, birinchi va oxirgi kun ham ichida. Muddat tugagach kursant oddiy navbatga qaytadi, o‘tkazilgan navbatlar qarz bo‘lib yig‘ilmaydi (algoritm 4-bo‘lim: haftalik/jami hisob bo‘yicha o‘zi oldinga qo‘yadi).
      - Tugash sanasi majburiy: aniq bo‘lmasa taxminiy, keyin “Muddatni uzaytirish” (faqat oldinga).
      - “Sog‘ayib qaytdi” — tugash sanasi joriy sutka (`current_duty_date`), kursant keyingi sutkadan navbatda. Faqat boshlangan va hali tugamagan yozuvda.
      - Boshlangan yozuvning boshlanish sanasi o‘zgarmaydi va yozuv o‘chirilmaydi; kelgusidagini o‘chirish mumkin (36-band).
      - Ustma-ust yozuv kiritilmaydi.
    - **Jurnal:** `sick_add`, `sick_edit`, `sick_extend`, `sick_recover`, `sick_delete` (kursant bilan; tafsilotlar o‘zbekcha, tavsif bilan).
    - **Naryadga ta’siri:**
      - almashtirish oynasida kasal kursant “Kasal: sana–sana” sababi bilan tanlab bo‘lmaydi;
      - qoralamada — sariq ogohlantirish va shu o‘ringa “Almashtirish” tugmasi, sutka tasdiqlanmaydi (32-band);
      - tasdiqlangan sutka O‘ZGARMAYDI — kiritishda va sutka sahifasida adminga “… sutkada naryadda, u tasdiqlangan. Almashtirish uchun avval tasdiqni bekor qiling.”;
      - kasal zalyotchi — mavjud ogohlantirish, jazo naryadi sog‘aygach davom etadi.
    - **Kim nimani ko‘radi:**
      - admin — hammasini, tavsif bilan;
      - kursantning o‘zi — bosh sahifada kartochka o‘rnida faqat “Siz kasallar ro‘yxatidasiz: 15.10 dan 20.10 gacha”, tavsifsiz;
      - boshqa kursantlar — hech narsa: ro‘yxat, sutka sahifasi va PDF’da belgi yo‘q;
      - guruh komandiri (19-bosqich) faqat “kasal, sana–sana”ni ko‘radi — tavsif shuning uchun alohida maydonda.
    - **Hujjat rasmi** yo‘q (18-bosqichda qo‘shiladi).
65. **Platforma nomi E-NARYAD (18-bosqich, 1.9.0):**
    - Nom hamma tilda bir xil, tarjima qilinmaydi. Yagona manba — `settings.SITE_NAME`.
      - Shablonlar `platform_name` kontekst o‘zgaruvchisini ishlatadi (`naryad.context_processors.ui`). `site_name` ishlatilmaydi: Django kirish sahifasi uni sayt domeni bilan almashtiradi.
      - Kontekst protsessori ishlamaydigan 500 sahifasida `{% load branding %}{% site_name %}`.
      - Boshqaruv paneli (`NaryadAdminSite`) va ilova nomi ham `settings.SITE_NAME` dan oladi. Qo‘lda qattiq yozilmaydi.
    - Brauzer tab nomi: `<sahifa> — E-NARYAD`. Yuqori panelda nom va “Bojxona instituti · 2-kurs” izohi (2-kurs — joy ma’nosida, nomda emas).
    - “Sutkalik naryad” hujjat ma’nosida qoladi (“sutkalik naryadlar ro‘yxati”, PDF, sutka sahifasi).
    - **PDF naryad shakli O‘ZGARMAYDI**, faqat metama’lumotda `Creator: E-NARYAD` (`<meta name="generator">`).
    - Ichki nomlar o‘zgarmaydi: `naryad` paketi va ilovasi, migratsiyalar, baza jadvallari, URL’lar, Docker/Railway nomlari (`sutkalik-naryad` image), repozitoriy papkasi.
    - Zip nomi 1.9.0 dan: `e-naryad-vX.Y.Z.zip`.
66. **Kasallik hujjatlari — rasmlar (18-bosqich, 1.9.0):**
    - **Model** `SickDocument` (`naryad/documents.py`):
      - UUID kalit, `Absence` ga CASCADE;
      - tur: kasallik varaqasi / tibbiy punkt ma’lumotnomasi / boshqa; ixtiyoriy izoh;
      - JPEG rasm va kichik rasm ma’lumotlar bazasida (`BinaryField`), chunki Railway disk vaqtinchalik. Rasmlar zaxira nusxaga kiradi (`pg_dump`, `dumpdata`).
      - Standart menejer baytlarni `defer` qiladi, faqat ko‘rish view’i `with_bytes()` bilan oladi.
    - **Yuklash** — faqat admin (`sick.manage`):
      - bitta kasallik yozuviga ≤ 5 rasm, har biri ≤ 8 MB;
      - turi mazmuni bo‘yicha (Pillow): JPEG/MPO, PNG, WEBP; HEIC — aniq xabar bilan rad;
      - ≤ 50 Mpiksel; EXIF orientatsiya qo‘llanadi, rasm qayta JPEG qilib yoziladi (metama’lumot, GPS o‘chadi), uzun tomoni ≤ 2000 px, sifat 85, kichik rasm 360 px.
    - **Jurnal:** `doc_add`, `doc_replace`, `doc_delete` — tur va yozuv sanalari, rasm mazmuni yozilmaydi. Kasallik yozuvi o‘chirilsa, rasmlari ham o‘chadi va jurnalga soni yoziladi. Hujjatlar sutkalarga ta’sir qilmaydi.
    - **Ko‘rish** `/kasal/<absence_id>/hujjat/<UUID>/` (`?kichik=1`):
      - faqat admin yoki o‘sha kursant (`documents.own`, faqat ko‘rish); boshqa kursant va guruh komandiri (19-bosqichda ham) — 403, kirmagan — kirish sahifasi;
      - sarlavhalar: `Cache-Control: private, no-store`, `X-Content-Type-Options: nosniff`, `X-Robots-Tag: noindex`;
      - ommaviy media URL yo‘q.
    - **Interfeys:**
      - kasallar ro‘yxatida “📎 n · Hujjatlar” yoki “Hujjat yo‘q” (majburiy emas);
      - yozuv sahifasida galereya: CSS `:target` lightbox, JavaScript yo‘q, CSP o‘zgarmaydi; yuklash formasi `accept="image/*"` (telefon kamerasi);
      - kursant kartochkasida “Kasallik hujjatlari — Hujjatlaringiz: n ta”, tavsifsiz (64-band).
67. **Guruh komandiri roli va “Mening guruhim” (19-bosqich, 1.10.0):**
    - **Rollar:** admin, kursant, `commander` (guruh komandiri). Komandir — kursant ham; uning barcha kursant imkoniyatlari (16-bosqich) saqlanadi va ustiga faqat ko‘rish uchun “Mening guruhim” qo‘shiladi. Bu bosqichda hech narsa kiritmaydi (zalyot — 20-bosqichda).
    - **Kimga beriladi:**
      - faqat guruh komandiri lavozimidagi faol kursantga (`Cadet.is_group_commander`: `duty_exempt` va lavozim “… guruh komandiri” bilan tugaydi; o‘rinbosar, starshina, pisar, kaptyorchik — yo‘q);
      - guruh kursantning guruhidan olinadi, komandir uni tanlamaydi;
      - har guruhga bitta faol komandir akkaunti (`User.clean_commander`).
    - **Akkauntlar:** `create_cadet_accounts`, boshqaruv panelidagi “Akkaunt yaratish (Excel)” va “Vaqtinchalik parol berish (Excel)”. Komandirga rol avtomatik. `must_change_password` komandirga ham amal qiladi.
    - **Doira** — yagona joy `naryad/group_scope.py`:
      - `scoped_cadets(user)` = o‘z guruhining faol kursantlari;
      - `commander_required` dekoratori (ruxsat `group.view` + doira);
      - boshqa guruh id’si — 404 (mavjudligi oshkor bo‘lmaydi);
      - URL parametri bilan guruhni o‘zgartirib bo‘lmaydi;
      - lavozimidan bo‘shagan yoki faolsiz komandir — 403.
    - **Ko‘rinadi:**
      - faqat TASDIQLANGAN sutkalar: navbatdagi va oxirgi naryad (sana, joy, lavozim);
      - holat: “Hozir naryadda” / “Kasal: sana–sana” / “Naryadga chiqmaydi” (lavozim matnisiz);
      - jonli sonlar, joriy va keyingi hafta jadvali, familiya bo‘yicha qidiruv.
    - **Ko‘rinmaydi:**
      - qoralamalar; kasallik tavsifi va hujjat rasmlari (URL — 403); sababli holat va ozodlik sabablari; zalyot;
      - statistika, jurnal, sozlamalar, admin bo‘limlari va har qanday o‘zgartirish (POST — 403);
      - boshqa guruhlarning alohida ma’lumotlari — faqat umumiy tasdiqlangan ro‘yxat, oddiy kursant darajasida.
    - Komandirning bosh sahifasida “Mening naryadim” o‘rnida “Mening guruhim” kartochkasi (komandir naryadga chiqmaydi).
68. **Komandir zalyot kiritadi va zalyot hisobi (20-bosqich, 1.11.0):**
    - **Zalyot qoidalari o‘zgarmaydi** (61-, 62-bandlar): faqat 1-NO‘J / 1-Yotoqxona, posbon, tasdiqlanganda “o‘tildi”, adolat hisobiga kirmaydi, PDF’da “zalyot” yo‘q, generator o‘zgarmaydi.
    - **Kim kiritadi:**
      - admin — istalgan kursantga, 1–10 ta;
      - guruh komandiri (`penalty.group` + guruh doirasi, 67-band) — faqat o‘z guruhining o‘g‘il, faol, naryadga chiqadigan kursantiga.
    - **Komandir cheklovlari** — `Setting`, serverda `penalties.commander_error`:
      - bir kiritishda ≤ `commander_penalty_max` (3);
      - tanbeh sanasi kelajakda emas (hamma uchun) va ≤ `commander_order_max_age_days` (30) kun eski;
      - kuniga ≤ `commander_daily_limit` (5) kiritish.
    - **Kiritish tartibi:**
      - forma → tasdiqlash sahifasi → saqlash; zalyot darhol faol;
      - bir xil kursant + sana + sabab 60 soniya ichida qayta yaratilmaydi (`DuplicateEntry`);
      - faol zalyotga qo‘shilsa — soni qo‘shiladi, alohida `PenaltyEntry` va jurnal yozuvi.
    - **Ko‘rib chiqish:** komandir kiritgan yoki qo‘shgan zalyot `reviewed_at = NULL` — “Yangi”. Admin bannerida soni, “Ko‘rib chiqildi” faqat belgini oladi.
    - **Tahrir va bekor qilish** — faqat admin (komandirga 403): kursantdan boshqa hamma maydon; soni ≥ o‘tilgan; jurnalga eski → yangi.
    - **Hisob** (`penalties.ledger`):
      - kiritilgan — tanbeh sanasi davrga tushgan `PenaltyEntry`;
      - o‘tildi — davrdagi tasdiqlangan jazo naryadlari;
      - qoldi — hozirgi faol zalyotlar qoldig‘i;
      - kesimlar: guruh, kursant, kim kiritdi; Excel varaqlari o‘zbekcha.
      - Komandir faqat o‘z guruhining jami ko‘rsatkichlarini ko‘radi.
    - **Kursant** o‘z zalyotini ko‘radi (61-band), kim kiritganini ko‘rmaydi; boshqa kursantlar hech narsa ko‘rmaydi.
69. **Sinov ma’lumotlarini to‘liq tozalash (20-bosqich, 1.11.0):**
    - `naryad/cleanup.py`, sahifa `/sozlamalar/tozalash/` (`settings.manage`) va `python manage.py clear_test_data [--dry-run] [--confirm TOZALASH --confirm2 "HAMMASI NOL"]`.
    - **O‘chadi:** `DutyWeek`, `DutyDay` (qoralama va tasdiqlangan, import qilingan ham), `Assignment` (oddiy va jazo), `GroupPostAssignment`, `PublishedDuty`, `Penalty`, `PenaltyEntry`, butun `ChangeLog`. Keyin jurnalda bitta `test_data_cleared` yozuvi.
    - **Qoladi:** kursantlar, guruhlar, joylar, foydalanuvchilar, `Setting`, `InitialRotation`, `PrepNote`, lavozim / `duty_exempt`, `Absence` va kasallik hujjatlari, login cheklovlari.
    - **Tartib:**
      - ko‘rib chiqish (hech narsa o‘zgarmaydi, holat izi `token`);
      - ikki so‘z;
      - avtomatik zaxira `settings.BACKUP_DIR` ga (`dumpdata --natural-foreign`, `.json.gz`) — muvaffaqiyatsiz bo‘lsa o‘chirilmaydi;
      - bitta tranzaksiya. Izi mos kelmasa yoki o‘chiradigan narsa qolmagan bo‘lsa — rad.
    - **Tiklash:** `migrate` → `flush --no-input` → `loaddata zaxira_….json.gz`.
    - **Tozalashdan keyin** navbat zanjiri `InitialRotation` dan boshlanadi (Sozlamalarda ko‘rinadi va o‘zgaradi). Birinchi sutka ochilgan haftada bo‘sh tarixdan tuziladi (14-band).
