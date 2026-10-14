# 1-bosqich: talablar, texnologiyalar steki va ma’lumotlar bazasi sxemasi

> Manbalar: `CLAUDE.md` (1–9-bo‘limlar), `docs/Naryad_tartiblangan.docx`, `data/2-KURS ROYXATI.doc`, 1-bosqich prompti.
> **Holat:** 1-bosqich savollariga javoblar olindi (5-bo‘lim) va `CLAUDE.md` ning 10-bo‘limiga yozildi. Hujjat shu qarorlarga moslab yangilangan.

---

## 1. Taqsimlash qoidalari — mening tushunishim

### 1.1. Vaqt birliklari
- **Sutka** — kun soat 18:00 dan ertasi kuni 18:00 gacha. Sutka o‘zi boshlangan sana bilan nomlanadi: “18-sentabr sutkasi” = 18.09 18:00 → 19.09 18:00 (PDF’da “18-sentabr kunidan 19-sentabr kuniga”).
- **2-kurs haftasi** — yakshanba 18:00 dan keyingi yakshanba 18:00 gacha, ya’ni 7 sutka (yakshanba, dushanba, …, shanba sanalari bilan boshlanadigan sutkalar). Kurslar naryadga haftama-hafta navbat bilan chiqadi; 2-kurs haftalari orasida boshqa kurslar turadi va platforma u haftalarda ishlamaydi. Interval kodga qotirilmaydi: keyingi hafta sanasi faqat taklif qilinadi, admin tasdiqlaydi.

### 1.2. Joylar va o‘rinlar (qat’iy)
Har sutka 20 o‘rin: 17 ta o‘g‘il bolalar uchun 6 ta joyda (Markaz 1, 1-NO‘J 4, 2-NO‘J 3, 1-Yotoqxona 3, O‘quv binosi 2, Patrul 4) va 3 ta qizlar uchun Qizlar yotoqxonasida. Joy va lavozimlar soni hech kim tomonidan o‘zgartirilmaydi — bazada “qulflangan” ma’lumot.

### 1.3. 1-daraja: qaysi guruh qaysi joyga (faqat o‘g‘il bolalar)
1. Har sutka 6 guruhning har biri 6 ta o‘g‘il joyidan **aynan bittasini to‘liq** beradi (1-NO‘J tushgan guruh 4 kishini to‘liq beradi).
2. Ertasiga har guruh zanjirda **keyingi** joyga o‘tadi: Markaz → 1-NO‘J → 2-NO‘J → 1-Yotoqxona → O‘quv binosi → Patrul → Markaz. Shuning uchun bir guruh ketma-ket ikki sutka bir joyda turmaydi.
3. Yangi 2-kurs haftasining 1-sutkasi oldingi 2-kurs haftasining oxirgi (7-) sutkasidan bir qadam davom etadi.
4. Natija: 7 sutkalik haftada guruh 6 joyni bir martadan o‘taydi, 1-sutkadagi joyi 7-sutkada yana takrorlanadi. Keyingi haftada zanjir bir qadam suriladi, shuning uchun takrorlanadigan joy ham har hafta boshqa bo‘ladi (6 haftada hammasi bir xil).
5. Guruhning haftalik yuki: 17 + (takrorlangan joy hajmi) = 18…21 o‘rin. Guruhlarda 13–17 o‘g‘il bor, demak har hafta har bir o‘g‘il kamida bir marta, ba’zilari ikki marta turadi.

### 1.4. 2-daraja: guruh ichidan kim (o‘g‘il bolalar)
1. Guruhga joy tushgach, shu guruhning **faol, sababsiz yo‘q bo‘lmagan** o‘g‘il kursantlaridan nomzodlar olinadi.
2. **Kecha (oldingi sutkada) naryadda bo‘lganlar** chiqarib tashlanadi. Boshqa odam yetmasa ham olinmaydi: o‘rin bo‘sh qoladi, qoralamaga ogohlantirish yoziladi va o‘rinni admin qo‘lda to‘ldiradi (2-bosqichda yangilangan, CLAUDE.md 10-bo‘lim, 13-band).
3. Nomzodlar quyidagi kalit bo‘yicha saralanadi va kerakli sondagi birinchilar olinadi:
   1. shu haftada necha marta turgan — kami oldin, **qat’iy**: guruhda hamma bir marta turmaguncha hech kim ikkinchi marta tushmaydi;
   2. jami naryadlar soni (oxirgi naryadi ham shu joy bo‘lsa, +1 jarima);
   3. oxirgi naryadi shu joy bo‘lganlar orqaga;
   4. shu joyda necha marta turgan — kami oldin;
   5. oxirgi naryad sanasi — uzoqroq dam olgan oldin;
   6. teng bo‘lsa — sana + kursant asosidagi deterministik “tasodif” (alifbo emas; bir xil kirishda doim bir xil natija).
4. Adolat hisobi **guruh ichida** yuritiladi: kursant faqat o‘z guruhdoshlari bilan solishtiriladi.
5. **Lavozimlar:** tanlangan 2–4 kishining barcha joylashuvlari (ko‘pi bilan 4! = 24 ta) ko‘rib chiqiladi. Har kim shu lavozimda kamroq turgan va oxirgi lavozimi takrorlanmaydigan variant tanlanadi (Markazda bitta o‘rin, Patrulda hammasi “posbon” — tanlov yo‘q).

### 1.5. Qizlar
- Faqat Qizlar yotoqxonasi, har sutka 3 kishi (navbatchi + 2 posbon).
- Guruhga bog‘lanmaydi: 13 qiz — bitta umumiy navbat. Saralash kaliti va cheklovlar o‘g‘il bolalarniki bilan bir xil (haftalik qat’iy navbat, kecha turgan olinmaydi, lavozim almashinuvi), faqat “guruh” o‘rnida 13 qizning umumiy hovuzi.
- Haftalik yuk: 7 × 3 = 21 o‘rin / 13 qiz → har hafta har qiz 1 yoki 2 marta.

### 1.6. Jarayon qoidalari
- Sutka: **qoralama → ko‘rib chiqish (qo‘lda tuzatish mumkin) → tasdiqlash**. Tarix va statistikaga **faqat tasdiqlangan** sutkalar kiradi.
- Qo‘lda almashtirishda sabab majburiy va `change_log` jurnaliga yoziladi: kim, qachon, kimni kimga, nima sababdan.
- Faolsizlantirilgan kursant o‘chirilmaydi, tarixi saqlanadi.

### 1.7. Hisob-kitob bilan tekshiruv (qoidalar bir-biriga zid emas)
- Ketma-ket ikki sutkada bir guruhdan olinadigan eng ko‘p odam: 1-NO‘J (4) + 2-NO‘J (3) = 7. Eng kichik guruhda (YuP-125) 13 o‘g‘il bor, ya’ni “kecha turgan olinmaydi” qoidasi oddiy holatda doim bajariladi. Faqat bir nechta kursant bir vaqtda kasal yoki ta’tilda bo‘lsa, ogohlantirish chiqishi mumkin.
- Qizlar: ketma-ket ikki sutkada 6 kishi kerak, 13 kishi bor — muammo yo‘q.

---

## 2. `2-KURS ROYXATI.doc` tekshiruvi

Fayl matnga aylantirildi (LibreOffice, UTF-8). Jins faylda yo‘q, shuning uchun CLAUDE.md dagi 13 ta qiz familiyasi bo‘yicha belgilandi; qo‘shimcha tekshiruv sifatida otasining ismi qo‘shimchasi ham tekshirildi (“qizi”, “-ovna/-evna” — aynan shu 13 kishida).

| Guruh | Ro‘yxatda jami | O‘g‘il | Qiz | CLAUDE.md 2-bo‘lim (jami / o‘g‘il / qiz) | Holat |
|---|---|---|---|---|---|
| YuP-125 | 15 | 13 | 2 | 15 / 13 / 2 | ✅ mos |
| BI-225 | 17 | 14 | 3 | 17 / 14 / 3 | ✅ mos |
| BI-325 | 16 | 14 | 2 | 16 / 14 / 2 | ✅ mos |
| BI-425 | 17 | 15 | 2 | 17 / 15 / 2 | ✅ mos |
| BI-525 | 17 | 17 | 0 | 17 / 17 / 0 | ✅ mos |
| BI-625 | 18 | 14 | 4 | 18 / 14 / 4 | ✅ mos |
| **Jami** | **100** | **87** | **13** | 100 / 87 / 13 | ✅ mos |

13 ta qizning hammasi ro‘yxatdan topildi: YuP-125 — Abduvaliyeva, Shamsiddinova; BI-225 — Abdullayeva, Karimova, Quvatova; BI-325 — Mamirova, Zoirova; BI-425 — Baxtiyorova, Panjiyeva; BI-625 — Azizova, Maxmudova, Muxammadiyeva, Ordabaeva.

**Sonlarda farq yo‘q.** Lekin ism yozilishida e’tibor beriladigan joylar bor (5-bo‘limdagi savollarda):

| Namuna PDF/docx’da | Ro‘yxatda | Izoh |
|---|---|---|
| Mehmonov Sh (YuP-125) | Mexmonov Shoxrux | “h/x” farqi (CLAUDE.md ham “Mexmonov Sh” deydi) |
| Yo‘ldoshov M (BI-525) | Yuldoshov Muxammadali | “Yo‘/Yu” farqi |
| Mahmudova H (BI-625) | Maxmudova Hayotxon | “h/x” farqi |
| Aslonov A (BI-525) | Aslonov Asliddin (BI-525) **va** Aslonov Anvar (BI-425) | Qisqa shakl bir xil — guruh ustuni ajratadi |
| — | Shavkatov Yahyobek (YuP-125), Shavkatov Shaxzod (BI-325) | Qisqa shakllar har xil: “Shavkatov Y”, “Shavkatov Sh” |
| — | Raximov Sardorbek (BI-525), Raximov Elyor (BI-625) | Qisqa shakllar har xil |

Yana: ro‘yxatda tutuq/o‘ belgilari aralash (`o‘g‘li`, `o‘g‘li`, `o'g'li`, `Ma’ruf`, `Ma'murjonovich`), qoraqalpoqcha harflar ham bor (`uǵli`, `ulí`, `Dástan`). To‘liq ro‘yxat — 6-bo‘lim (ilova).

---

## 3. Texnologiyalar steki — tasdiq va aniqlashtirishlar

Stek **tasdiqlanadi**. Asosiy texnologiya o‘zgarmaydi, faqat aniqlashtirishlar:

| Qism | Tanlov | Asos |
|---|---|---|
| Til | Python 3.12 | Kelishilgan |
| Framework | **Django 5.2 LTS** | LTS — 2028-yil aprelgacha xavfsizlik yangilanishlari |
| Ma’lumotlar bazasi | PostgreSQL 16 (Railway), ishlab chiqishda SQLite | `dj-database-url` orqali `DATABASE_URL` dan |
| Foydalanuvchi modeli | **Custom `User` (AbstractUser + `role`)** — loyiha boshidanoq | Django’da keyin almashtirish juda qiyin |
| Interfeys | Django shablonlari + HTMX 2 (static faylda, CDN’siz) + Tailwind CSS | Tailwind **standalone CLI** (Node.js kerak emas) — Docker build’da CSS yig‘iladi |
| Statik fayllar | WhiteNoise | Railway’da alohida server kerak bo‘lmaydi |
| Server | Gunicorn | Railway uchun standart |
| PDF | WeasyPrint | Docker’da Pango kutubxonalari o‘rnatiladi. **Shrift: Times New Roman** (qaror 9). Docker image’ga Microsoft core fonts (`ttf-mscorefonts-installer`) o‘rnatiladi; build paytida yuklab bo‘lmasa, `.ttf` fayllar `naryad/static/fonts/` ga qo‘yiladi. Zaxira (fallback) shrift — Liberation Serif |
| Excel | openpyxl | Import va (ixtiyoriy) eksport |
| Algoritm | `naryad/engine/allocator.py` — Django’siz toza Python, `dataclass` kirish/chiqish | pytest + `pytest-django` (model testlari uchun) |
| Vaqt zonasi | `TIME_ZONE = "Asia/Tashkent"`, `USE_TZ = True` | Sutka chegarasi 18:00 mahalliy vaqtda |
| Konteyner | Dockerfile + docker-compose (web + postgres) | Lokal ishlab chiqish va Railway bir xil image |
| Deploy | Railway (Dockerfile, Railway PostgreSQL) | Kelishilgan |
| Sifat | ruff (lint + format) | Bitta tez vosita |

Boshlang‘ich ma’lumotlar: `.doc` faylni ilova o‘zi o‘qimaydi. Ro‘yxat bir marta CSV/Excel’ga o‘tkaziladi (men tayyorlab beraman) va **Excel import** orqali yoki boshlang‘ich buyruq (`manage.py seed_cadets`) bilan yuklanadi.

---

## 4. Ma’lumotlar bazasi sxemasi

> **3-bosqichdagi aniqlashtirishlar (Django modellari):**
> - `setting` — kalit/qiymat jadvali o‘rniga **yagona yozuvli** jadval (pk = 1): `recipient_position`, `recipient_name`, `course_head_position`, `course_head_rank`, `course_head_name`, `course_number`. Sutka soati (18:00) `naryad/engine/config.py` da.
> - `assignment.is_manual` o‘rniga `assignment.source` (`auto` / `manual`); `post_slot.pdf_label` → `print_label`; `post.rotation_order` → `rotation_index`.
> - `duty_week.created_by`, `absence.created_by`, `change_log.user` — bo‘sh bo‘lishi mumkin (tizim amallari, buyruqlar).
> - `post` va `post_slot` migratsiya bilan to‘ldiriladi (`naryad/migrations/0002_posts_and_settings.py`).

### 4.1. Umumiy kelishuvlar
- Har jadvalda `id` — `BIGINT` avtomatik birlamchi kalit (PK).
- **Model nomi va jadval nomi:** `group` va `user` SQL’da zahiralangan so‘zlar va Django’ning o‘z `Group`/`User` modellari bilan to‘qnashadi. Shuning uchun modellar `StudyGroup` → `study_group` va `User` → `app_user` deb nomlanadi; mantiqan CLAUDE.md 8-bo‘limdagi jadvallarning aynan o‘zi.
- “Majburiy” = `NOT NULL` (va matnda bo‘sh bo‘lmasligi forma darajasida tekshiriladi).
- O‘chirish siyosati: tarixga tegishli bog‘lanishlar `PROTECT` (kursant, guruh, joy tarix bor ekan o‘chirilmaydi — faolsizlantiriladi).
- Statistika saqlanmaydi — `assignment` (faqat `duty_day.status = 'approved'`) dan hisoblanadi.

### 4.2. Jadvallar

#### `study_group` (CLAUDE.md: `group`) — guruhlar; rotatsiya va adolat hisobi shu kesimda
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| code | varchar(20) | ha | **UNIQUE**. `YuP-125`, `BI-525` |
| direction | varchar(100) | ha | “Yurisprudensiya”, “Bojxona ishi” |
| language | varchar(2) | ha | `uz` / `ru` (default `uz`) |
| display_order | smallint | ha | **UNIQUE**. Ro‘yxat va hisobotlarda tartib |
| is_active | boolean | ha | default `true` |

#### `cadet` — kursantlar bazasi (qo‘shish, tahrir, faolsizlantirish, import)
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| group_id | FK → study_group | ha | `PROTECT` |
| last_name | varchar(60) | ha | Familiya |
| first_name | varchar(60) | ha | Ism |
| patronymic | varchar(100) | yo‘q | Otasining ismi qo‘shimchasi bilan (“Bekzod o‘g‘li”) |
| gender | char(1) | ha | `M` / `F`. CHECK |
| list_number | smallint | yo‘q | Guruh ro‘yxatidagi tartib raqami |
| short_name_override | varchar(60) | yo‘q | PDF qisqa shaklini qo‘lda belgilash (odatda bo‘sh — avtomatik hisoblanadi: “Familiya + bosh harf”, Sh/Ch/G‘/O‘/Ng saqlanadi) |
| is_active | boolean | ha | default `true` |
| deactivated_at | timestamptz | yo‘q | |
| deactivation_reason | varchar(200) | yo‘q | `is_active = false` bo‘lsa majburiy (CHECK) |
| duty_exempt | boolean | ha | default `false`. Naryaddan ozod (komandirlar, kurs lavozimlari): faol, lekin naryadga qo‘yilmaydi (CLAUDE.md 10-bo‘lim, 56-band) |
| duty_position | varchar(100) | yo‘q | Lavozimi; `duty_exempt = true` bo‘lsa majburiy (CHECK) |
| created_at / updated_at | timestamptz | ha | |

Cheklovlar: **UNIQUE (group_id, last_name, first_name, patronymic)** — importda dublikat bo‘lmasin; **UNIQUE (group_id, list_number)** (NULL’lar bundan mustasno). Indeks: `(gender, is_active)`.

#### `post` — navbatchilik joylari (7 ta, qulflangan)
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| code | varchar(20) | ha | **UNIQUE**. `markaz`, `noj1`, `noj2`, `yotoq1`, `oquv`, `patrul`, `qizlar` |
| name | varchar(100) | ha | “1-NO‘J bo‘yicha” |
| section_title | varchar(100) | ha | PDF’dagi bo‘lim sarlavhasi |
| gender | char(1) | ha | `M` / `F`. CHECK |
| display_order | smallint | ha | **UNIQUE**. PDF tartibi 1…7 |
| rotation_order | smallint | yo‘q | **UNIQUE**. Zanjirdagi o‘rni 0…5 (Markaz 0 → Patrul 5); qizlar joyida `NULL`. CHECK: `gender='M'` ⇔ `rotation_order IS NOT NULL` |

#### `post_slot` — joy ichidagi o‘rinlar/lavozimlar (20 ta, qulflangan)
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| post_id | FK → post | ha | `PROTECT` |
| position | smallint | ha | Joy ichidagi tartib 1…4 |
| role | varchar(30) | ha | `navbatchi` / `navbatchi_yordamchisi` / `posbon` |
| pdf_label | varchar(150) | ha | “1-NO‘J bo‘yicha navbatchi”, “Kurs bo‘yicha posbon” |
| show_label | boolean | ha | PDF’da yozuv ko‘rsatilsinmi (Patrulda faqat 1-qator `true`) |

Cheklov: **UNIQUE (post_id, position)**. `post` va `post_slot` migratsiya bilan to‘ldiriladi va interfeysda tahrirlanmaydi — CLAUDE.md 3-bo‘lim talabi.

#### `duty_week` — 2-kurs haftasi
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| start_date | date | ha | **UNIQUE**. Faqat yakshanba (CHECK: `EXTRACT(ISODOW FROM start_date) = 7`). Hafta shu kuni 18:00 da boshlanadi |
| note | varchar(200) | yo‘q | |
| created_by_id | FK → app_user | ha | `PROTECT` |
| created_at | timestamptz | ha | |

Haftalar ustma-ust tushmasligi: `start_date` lar orasidagi farq ≥ 7 kun (ilova darajasida tekshiriladi, chunki bu bir necha qatorga taalluqli shart). Yangi hafta ochilganda tizim **oldingi 2-kurs haftasi + `week_interval_days`** sanasini taklif qiladi (sozlama, boshlang‘ich qiymati 14; kurslar soni o‘zgarsa admin o‘zgartiradi), admin sanani tasdiqlaydi yoki o‘zgartiradi.

#### `duty_day` — sutka (status: draft/approved)
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| week_id | FK → duty_week | ha | `PROTECT` |
| date | date | ha | **UNIQUE**. Sutka boshlangan sana (18:00) |
| status | varchar(10) | ha | `draft` / `approved`. CHECK |
| warnings | jsonb | ha | Generator ogohlantirishlari ro‘yxati, default `[]` |
| generated_by_id | FK → app_user | yo‘q | Qoralamani kim tuzdi |
| generated_at | timestamptz | yo‘q | |
| approved_by_id | FK → app_user | yo‘q | |
| approved_at | timestamptz | yo‘q | |

CHECK: `status='approved'` ⇒ `approved_by_id` va `approved_at` NOT NULL. Ilova darajasida: `week.start_date ≤ date ≤ week.start_date + 6`; tasdiqlash uchun 20 ta `assignment` to‘liq bo‘lishi shart.

#### `group_post_assignment` — 1-daraja: sutkada qaysi guruh qaysi joyda
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| duty_day_id | FK → duty_day | ha | `CASCADE` (qoralama o‘chsa, birga) |
| post_id | FK → post | ha | Faqat o‘g‘il joylari |
| group_id | FK → study_group | ha | `PROTECT` |

Cheklovlar: **UNIQUE (duty_day_id, post_id)**, **UNIQUE (duty_day_id, group_id)** → har sutka 6 qator, har guruh bitta joy. Zanjir davomi shu jadvaldan olinadi: oldingi sutkadagi qatorlar → bir qadam surish.

#### `assignment` — 2-daraja: kim qaysi o‘rinda (tarixning asosi)
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| duty_day_id | FK → duty_day | ha | `CASCADE` |
| post_slot_id | FK → post_slot | ha | `PROTECT` |
| cadet_id | FK → cadet | ha | `PROTECT` |
| group_id | FK → study_group | ha | Tayinlash paytidagi guruh (nusxa) — kursant keyin guruhini almashtirsa ham eski PDF va statistika to‘g‘ri qoladi |
| is_manual | boolean | ha | Qo‘lda qo‘yilganmi (default `false`) |
| created_at | timestamptz | ha | |

Cheklovlar: **UNIQUE (duty_day_id, post_slot_id)**, **UNIQUE (duty_day_id, cadet_id)** (CLAUDE.md 8-bo‘lim). Ilova darajasida: kursant jinsi = joy jinsi; o‘g‘il bolalarda `group_id` = shu sutkadagi `group_post_assignment` dagi guruh. Indeks: `(cadet_id, duty_day_id)` — tarix so‘rovlari uchun.

#### `absence` — sababli yo‘qlik (kasal, ta’til…), generator ularni olmaydi
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| cadet_id | FK → cadet | ha | `PROTECT` |
| start_date | date | ha | Birinchi sutka sanasi (shu sanadan boshlangan sutka) |
| end_date | date | ha | Oxirgi sutka sanasi, **ichida** (CHECK `end_date ≥ start_date`) |
| reason_type | varchar(20) | ha | `kasal` / `tatil` / `xizmat` / `boshqa` |
| note | varchar(300) | yo‘q | `boshqa` bo‘lsa majburiy |
| created_by_id | FK → app_user | ha | |
| created_at | timestamptz | ha | |

Indeks: `(cadet_id, start_date, end_date)`.

#### `change_log` — jurnal: kim, qachon, kimni kimga, nima sababdan
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| duty_day_id | FK → duty_day | ha | `PROTECT` (jurnal o‘chmaydi) |
| action | varchar(20) | ha | `generate` / `import` (o‘tgan tarixni qo‘lda kiritish) / `replace` / `swap` / `approve` / `reopen` (faqat admin) |
| post_slot_id | FK → post_slot | yo‘q | `replace`/`swap` da |
| old_cadet_id | FK → cadet | yo‘q | Kim olindi |
| new_cadet_id | FK → cadet | yo‘q | Kim qo‘yildi |
| reason | text | ha | `replace`, `swap`, `reopen` da bo‘sh bo‘lmasligi shart (CHECK) |
| user_id | FK → app_user | ha | Kim qildi |
| created_at | timestamptz | ha | Qachon |

#### `app_user` (CLAUDE.md: `user`) — tizim foydalanuvchilari va rollar
Django `AbstractUser` maydonlari (username, password, first_name, last_name, is_active, last_login …) + :

| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| role | varchar(10) | ha | `admin` (kurs boshlig‘i) / `cadet` (faqat ko‘rish). Tuzuvchi roli yo‘q (CLAUDE.md 10-bo‘lim, 26-band). CHECK |
| cadet_id | FK → cadet, **UNIQUE** (1:1) | yo‘q | Foydalanuvchi kursant bo‘lsa, o‘z tarixini ko‘rishi uchun |

#### `setting` — PDF sarlavhasi, qabul qiluvchi, imzo va boshqa sozlamalar (kodga yozilmaydi)
| Maydon | Turi | Majburiy | Izoh |
|---|---|---|---|
| id | bigint PK | ha | |
| key | varchar(50) | ha | **UNIQUE** |
| value | text | ha | |
| description | varchar(200) | yo‘q | Interfeysda ko‘rsatiladigan izoh |
| updated_by_id | FK → app_user | yo‘q | |
| updated_at | timestamptz | ha | |

Boshlang‘ich kalitlar: `recipient_text` (“Bojxona instituti Navbatchilik\nqismi boshlig‘i, podpolkovnik\nX.Sattorovga”), `course_title` (“2-kurs ro‘yxati”), `signer_position` (“Kurs boshlig‘i”), `signer_rank` (“mayor”), `signer_name` (“X.Turobov”), `duty_start_time` (“18:00”), `week_interval_days` (“14”).

### 4.3. Hafta va sutka qanday saqlanadi (alohida)

```
duty_week.start_date = 2026-09-13 (yakshanba)

 sutka  duty_day.date   haqiqiy vaqt oralig‘i
 ─────  ──────────────  ─────────────────────────────────────────
   1    2026-09-13 Ya   13.09 18:00 → 14.09 18:00
   2    2026-09-14 Du   14.09 18:00 → 15.09 18:00
   …
   6    2026-09-18 Ju   18.09 18:00 → 19.09 18:00   ← PDF: “18-sentabr kunidan 19-sentabr kuniga”
   7    2026-09-19 Sh   19.09 18:00 → 20.09 18:00   (hafta yakshanba 18:00 da tugaydi)

 keyingi 2-kurs haftasi: start_date = 2026-09-27 (+14 kun) — taklif, qo‘lda o‘zgartirsa bo‘ladi
```

- Bazada **faqat sanalar** saqlanadi (`date`), soat emas. Boshlanish/tugash vaqti hisoblanadi: `starts_at = date + duty_start_time`, `ends_at = starts_at + 24 soat` (Asia/Tashkent). Bu soat o‘zgarishi va vaqt zonasi xatolaridan himoya qiladi.
- “Kecha” = `date − 1` sanali sutka. Haftaning 1-sutkasi uchun “kecha” — oldingi kunda 2-kurs naryadi bo‘lmagan, shuning uchun cheklov amalda bo‘lmaydi.
- “Shu haftada necha marta” = `week_id` bir xil bo‘lgan **tasdiqlangan** sutkalardagi tayinlashlar.
- Zanjir davomi: yangi haftaning 1-sutkasi uchun “oldingi sutka” = `date < yangi sana` bo‘lgan eng oxirgi `duty_day` (odatda 8 kun oldingi shanba sutkasi).

### 4.4. Matnli ER-diagramma

```
                         ┌──────────────┐
                         │   setting    │   (mustaqil, key → value)
                         └──────────────┘

┌──────────────┐ 1     N ┌──────────────┐ 1     0..1 ┌──────────────┐
│ study_group  │────────<│    cadet     │────────────│   app_user   │
│ (group)      │         └──────────────┘  cadet_id  │ (user + role)│
└──────────────┘          │1   │1    │1              └──────────────┘
   │1      │1             │    │     │                 │1 (created_by, approved_by,
   │       │              │N   │N    │N                │   user …)
   │       │       ┌──────────┐│  ┌──────────────┐      │
   │       │       │ absence  ││  │  change_log  │>─────┘
   │       │       └──────────┘│  │ old/new cadet│
   │       │                   │  └──────────────┘
   │       │                   │         │N
   │       │N                  │N        │
   │  ┌─────────────────────┐  ┌──────────────┐ N   1 ┌──────────────┐
   │  │group_post_assignment│  │  assignment  │>──────│  post_slot   │
   │  │ UQ(day,post)        │  │ UQ(day,slot) │       │ UQ(post,pos) │
   │  │ UQ(day,group)       │  │ UQ(day,cadet)│       └──────────────┘
   │  └─────────────────────┘  └──────────────┘               │N
   │       │N        │N               │N                      │
   │       │         └──────┐  ┌──────┘                       │1
   │       │1               │1 │1                      ┌──────────────┐
   │  ┌──────────────┐ N  1 ┌──────────────┐           │     post     │
   │  │  duty_day    │>─────│  duty_week   │           │ (7 ta joy)   │
   │  │ date UQ      │      │ start_date UQ│           └──────────────┘
   │  │ draft/approved│     │ (yakshanba)  │                  │1
   │  └──────────────┘      └──────────────┘                  │
   │                                                          │
   └──── assignment.group_id (nusxa)    group_post_assignment.post_id ──┘
```

Qisqacha bog‘lanishlar:
- `study_group 1─N cadet`, `study_group 1─N group_post_assignment`, `study_group 1─N assignment` (nusxa)
- `post 1─N post_slot`, `post 1─N group_post_assignment`
- `duty_week 1─N duty_day`, `duty_day 1─N group_post_assignment`, `duty_day 1─N assignment`, `duty_day 1─N change_log`
- `post_slot 1─N assignment`, `cadet 1─N assignment`, `cadet 1─N absence`
- `cadet 1─0..1 app_user`; `app_user 1─N` (duty_week, duty_day, absence, change_log, setting — kim yaratdi/tasdiqladi)

### 4.5. Qaysi jadval qaysi funksiya uchun (bir qatorda)
| Jadval | Funksiya |
|---|---|
| study_group | 1-daraja rotatsiya va guruh kesimidagi adolat hisobi |
| cadet | Kursantlar bazasi: qo‘shish, tahrir, faolsizlantirish, Excel import |
| post | 7 ta joy, PDF bo‘lim tartibi va rotatsiya zanjiri |
| post_slot | Har joydagi qat’iy o‘rinlar va lavozimlar, PDF qator yozuvlari |
| duty_week | 2-kurs haftasi: “shu haftada necha marta” qoidasi va zanjirni haftadan haftaga ulash |
| duty_day | Sutka va uning holati (qoralama/tasdiqlangan) — tarixga faqat tasdiqlangani kiradi |
| group_post_assignment | Sutkada guruh→joy taqsimoti va keyingi sutka uchun zanjir davomi |
| assignment | Kim, qachon, qayerda, qaysi lavozimda — tarix, statistika va PDF manbai |
| absence | Kasal/ta’tildagilarni generatordan chiqarish |
| change_log | Qo‘lda tuzatishlar va tasdiqlash jurnali (sabab majburiy) |
| app_user | Kirish va rollar (admin, kursant) |
| setting | PDF sarlavhasi, qabul qiluvchi, imzo, sutka soati, hafta oralig‘i |

---

## 5. Qabul qilingan qarorlar (1-bosqich savollari)

| № | Savol | Qaror | Sxemaga ta’siri |
|---|---|---|---|
| 1 | CLAUDE.md 10-bo‘limi | Shart emas — javoblar shu jadvalda va CLAUDE.md 10-bo‘limiga yozildi | — |
| 2 | Haftalar oralig‘i | Kurslar haftama-hafta navbat bilan chiqadi. Interval qotirilmaydi | `duty_week.start_date` admin tasdiqlaydi; `week_interval_days` faqat taklif |
| 3 | Ism yozilishi manbasi | **Rasmiy ro‘yxat** asosiy (Mexmonov Sh, Yuldoshov M, Maxmudova H) | `cadet` ro‘yxatdan; kerak bo‘lsa `short_name_override` |
| 4 | Belgilarni birxillashtirish | **Ha** — importda `o‘/g‘` (U+02BB) va tutuq `’` (U+02BC) ga keltiriladi; qoraqalpoqcha harflar o‘zgarmaydi | Import funksiyasida normalizatsiya |
| 5 | Tasdiqlangan sutkani o‘zgartirish | **Faqat admin, sabab ko‘rsatib**: `reopen` → tuzatish → qayta tasdiqlash, hammasi jurnalga | `change_log.action = reopen`, `reason` majburiy |
| 6 | Qoralama tuzish tartibi | **Sutkama-sutka.** Bir haftalik qoralama birdan tuzilmaydi; keyingi sutka faqat oldingisi tasdiqlangach tuziladi | Ilova darajasida tekshiruv: bitta haftada bir vaqtda ko‘pi bilan bitta `draft` |
| 7 | Birinchi sutkadagi guruh→joy | **Admin qo‘lda kiritadi**, keyin zanjir avtomatik | Birinchi `group_post_assignment` qo‘lda |
| 8 | Oldingi qog‘oz tarixi | **Ha** — admin o‘tgan sutkalarni qo‘lda “tasdiqlangan” sifatida kiritadi | Qo‘lda kiritilgan `assignment.is_manual = true`, `change_log.action = generate` o‘rniga `import` |
| 9 | PDF shrifti | **Times New Roman** | Docker’da shrift o‘rnatiladi (3-bo‘lim) |
| 10 | Kursantlar kirishi | **Har kursantga login**; admin hisoblarni ommaviy yaratadi, parol birinchi kirishda almashtiriladi | `app_user.cadet_id` (1:1), `role = cadet` |
| 11 | Sababli yo‘qlik | Sutka sanalari bo‘yicha, ikkala chegara ichida | `absence.start_date … end_date` |
| 12 | “Hamma bir marta” qoidasi qizlarga | **Ha**, 13 qizning umumiy hovuzi uchun ham qat’iy | Algoritmda qizlar hovuzi uchun ham 1-kalit qat’iy |

Ochiq savol qolmadi.

---

## 6. Ilova: `2-KURS ROYXATI.doc` dan olingan to‘liq ro‘yxat

Jins CLAUDE.md dagi qizlar ro‘yxati bo‘yicha belgilangan. Ism-familiyalar fayldagidek, o‘zgartirilmagan.

**YuP-125** (15 kishi)

| № | F.I.Sh. (ro‘yxatdagidek) | Jins |
|---|---|---|
| 1 | Abduvaliyeva Ruxshona Otamurodovna | qiz |
| 2 | Abduqodirov Abdulqosim Abdulxakim o‘g‘li | o‘g‘il |
| 3 | Abduhamidov Asadbek Ma’ruf o‘g‘li | o‘g‘il |
| 4 | Axmadaliyev Jasurbek Muzaffar o‘g‘li | o‘g‘il |
| 5 | Badriyev Azizbek Abdulaziz o‘g‘li | o‘g‘il |
| 6 | Hakimjonov Ahmadjon Alisher o‘g‘li | o‘g‘il |
| 7 | Kazaxbayev Azizbek Kuralbayevich | o‘g‘il |
| 8 | Kukanov Asilbek Rizamat o‘g‘li | o‘g‘il |
| 9 | Latifjanov Elbek Oybek o‘g‘li | o‘g‘il |
| 10 | Mexmonov Shoxrux Yunus o‘g‘li | o‘g‘il |
| 11 | Oblaberdiyev Islomjon Keldiyor o‘g‘li | o‘g‘il |
| 12 | Tojiyev Sherali Tolmas o‘g‘li | o‘g‘il |
| 13 | Shamsiddinova Ruxsora Otabek qizi | qiz |
| 14 | Sharipov Muxtorbek Davronbek o‘g‘li | o‘g‘il |
| 15 | Shavkatov Yahyobek Vahhobjon o‘g‘li | o‘g‘il |

**BI-225** (17 kishi)

| № | F.I.Sh. (ro‘yxatdagidek) | Jins |
|---|---|---|
| 1 | Abdullayeva Marjona Abduali qizi | qiz |
| 2 | Anarbaev Ruslan Abdukadir uǵli | o‘g‘il |
| 3 | Ashuraliyev Botirjon Ma’murjonovich | o‘g‘il |
| 4 | Bayozov Baxtiyor Po‘Lotovich | o‘g‘il |
| 5 | Bo‘riyev Shohruxmirzo Norbobo o‘g‘li | o‘g‘il |
| 6 | Eshmatov Jobirbek Baxtiyor o‘g‘li | o‘g‘il |
| 7 | Ismatilloyev Azizbek To‘lqin o‘g‘li | o‘g‘il |
| 8 | Karimova Shahzoda Shuhrat qizi | qiz |
| 9 | Norbutayev Bekzod Saidvali o‘g‘li | o‘g‘il |
| 10 | Nuriddinov Ozodbek Shavkatovich | o‘g‘il |
| 11 | Orziqulov Jahongir Raziddin o‘g‘li | o‘g‘il |
| 12 | Ozodov Axmadjon Muxtorbek o‘g‘li | o‘g‘il |
| 13 | Quvatova Durdona Zafarjonovna | qiz |
| 14 | Umirov Yashin Ravshan o‘g‘li | o‘g‘il |
| 15 | Valiyev Jamshidbek Dilshodbek o‘g‘li | o‘g‘il |
| 16 | Shodiyev Ruslan Olimjon o‘g‘li | o‘g‘il |
| 17 | Shermamatov Dilshodbek Shaxobidin o‘g‘li | o‘g‘il |

**BI-325** (16 kishi)

| № | F.I.Sh. (ro‘yxatdagidek) | Jins |
|---|---|---|
| 1 | Abdusaidov Mirza Ulug‘bek o‘g‘li | o‘g‘il |
| 2 | Akramjonov Axmadjon Akramjon o‘g‘li | o‘g‘il |
| 3 | Amatov Zafarbek Zohidjon o‘g‘li | o‘g‘il |
| 4 | Begzodxonov Boburxon Begzodxon o‘g‘li | o‘g‘il |
| 5 | Botirov Shahriyor Umidovich | o‘g‘il |
| 6 | Ismoilov Sobirjon Valijon o‘g‘li | o‘g‘il |
| 7 | Jo‘rayev Shamshodbek Vahob o‘g‘li | o‘g‘il |
| 8 | Mamirova Mashxura Baxriddin qizi | qiz |
| 9 | Salimov Og‘abek Baxtiyor o‘g‘li | o‘g‘il |
| 10 | Saloxitdinov Hojiakbar Vohidjon o‘g‘li | o‘g‘il |
| 11 | Suyunov Asadbek Olimjon o‘g‘li | o‘g‘il |
| 12 | Uzaqbergenov Azizbek Sharapatdin ulí | o‘g‘il |
| 13 | Xayrillayev Javohir Oybek o‘g‘li | o‘g‘il |
| 14 | Xudoyberdiyev Ramazon Komilovich | o‘g‘il |
| 15 | Zoirova Sevara Dilshod qizi | qiz |
| 16 | Shavkatov Shaxzod Shuxratovich | o‘g‘il |

**BI-425** (17 kishi)

| № | F.I.Sh. (ro‘yxatdagidek) | Jins |
|---|---|---|
| 1 | Abduqahhorov Maxmudbek Muhammadali o‘g‘li | o‘g‘il |
| 2 | Aslonov Anvar Azizovich | o‘g‘il |
| 3 | Baxtiyorova Nozimaxon Olimjonovna | qiz |
| 4 | Bayirov Azizbek Erkin o‘g‘li | o‘g‘il |
| 5 | Bozorov Jo‘rabek Azamat o‘g‘li | o‘g‘il |
| 6 | Islomxonov Ramziddin Inomxon o‘g‘li | o‘g‘il |
| 7 | Karimjonov Anvarbek Baxtiyor o‘g‘li | o‘g‘il |
| 8 | Meyliqulov Sunnatbek Ernazar o‘g‘li | o‘g‘il |
| 9 | Mirzakarimov Olimjon Otabek o‘g‘li | o‘g‘il |
| 10 | Muxtoxiddinov Muxammadsodiq Muxitdin o‘g‘li | o‘g‘il |
| 11 | Navro‘zov Jasurbek Baxtiyor o‘g‘li | o‘g‘il |
| 12 | Nazarov Toxir Normat o‘g‘li | o‘g‘il |
| 13 | Panjiyeva Munisa Xusniddinovna | qiz |
| 14 | Rahmonov Sardor Mavlon o‘g‘li | o‘g‘il |
| 15 | Safarov Mirjalol Ahadjon o‘g‘li | o‘g‘il |
| 16 | Sayliyev Muhammad Javohirovich | o‘g‘il |
| 17 | G‘iyozov Izzatjon Inomjonovich | o‘g‘il |

**BI-525** (17 kishi)

| № | F.I.Sh. (ro‘yxatdagidek) | Jins |
|---|---|---|
| 1 | Abdulazizov Oyatillo Abduxalilovich | o‘g‘il |
| 2 | Aslonov Asliddin Davronovich | o‘g‘il |
| 3 | A’zamov Azizbek Davlatjon o‘g‘li | o‘g‘il |
| 4 | Bobomurodov Asilbek Alibek o‘g‘li | o‘g‘il |
| 5 | Gulliyev Shoxjahon Sherzodovich | o‘g‘il |
| 6 | Ismoiljonov Islomjon Isroiljon o‘g‘li | o‘g‘il |
| 7 | Maxsudov Hosilbek Baxtiyor o‘g‘li | o‘g‘il |
| 8 | Yuldoshov Muxammadali Bekzod o‘g‘li | o‘g‘il |
| 9 | Nekmurodov Fayyozbek Firdavs o‘g‘li | o‘g‘il |
| 10 | Niyozov Ulug‘bek Xoshimjonovich | o‘g‘il |
| 11 | Nosirjonov Abdulaziz Sultonali o‘g‘li | o‘g‘il |
| 12 | Raximov Sardorbek Alimardon o‘g‘li | o‘g‘il |
| 13 | Sa’dullayev Behro‘z Bahodir o‘g‘li | o‘g‘il |
| 14 | Sirojov Qodirbek Sanjar o‘g‘li | o‘g‘il |
| 15 | Turdimurodov Komron G‘iyosiddin o‘g‘li | o‘g‘il |
| 16 | Tursunov Saidasrorxon O‘tkir o‘g‘li | o‘g‘il |
| 17 | Qodirjanov Shaxrux Baxtiyorovich | o‘g‘il |

**BI-625** (18 kishi)

| № | F.I.Sh. (ro‘yxatdagidek) | Jins |
|---|---|---|
| 1 | Abdusattarov Bahodir Xayrulla o‘g‘li | o‘g‘il |
| 2 | Avazbayev Murat Maratovich | o‘g‘il |
| 3 | Azizova Sug‘diyona Jurabekovna | qiz |
| 4 | Erkinjonov Xushnudbek Elyorjon o‘g‘li | o‘g‘il |
| 5 | Mahmudov Saidakbar Sobirjon o‘g‘li | o‘g‘il |
| 6 | Maxmudova Hayotxon Oybek qizi | qiz |
| 7 | Mustayev Amir Zokirjonovich | o‘g‘il |
| 8 | Muxammadiyeva Xumora Valijon qizi | qiz |
| 9 | Muxammadjonov Abbosxon Akmaljon o‘g‘li | o‘g‘il |
| 10 | Narzullayev Odilbek Murodjon o‘g‘li | o‘g‘il |
| 11 | Ordabaeva Malika Timurovna | qiz |
| 12 | Parpiboyev Boburjon Bahodir o‘g‘li | o‘g‘il |
| 13 | Ramanov Dástan Jaksibay ulí | o‘g‘il |
| 14 | Raximov Elyor Ruslan o‘g‘li | o‘g‘il |
| 15 | Tursunmurodov Bahodir Xon Turdialijonovich | o‘g‘il |
| 16 | Xaitov Amal Anvarovich | o‘g‘il |
| 17 | O‘rmonjonov Muxammadqodir Jaxongir o‘g‘li | o‘g‘il |
| 18 | G‘ayratov G‘iyosiddin G‘ulomjon o‘g‘li | o‘g‘il |
