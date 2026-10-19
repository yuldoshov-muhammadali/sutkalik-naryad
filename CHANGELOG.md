# E-NARYAD — o‘zgarishlar tarixi

Format: [Keep a Changelog](https://keepachangelog.com/), versiyalar: [SemVer](https://semver.org/).

## [1.11.0] — 2026-10-19

20-bosqich: komandir zalyot kiritadi, zalyot hisobi, sinov ma’lumotlarini to‘liq tozalash (CLAUDE.md 68- va 69-bandlar). Zalyot qoidalari va generator o‘zgarmagan: zalyotchi bo‘lmasa natija bayt-bayt avvalgidek (84 sutkalik etalon xesh).

### Qo‘shildi — komandir zalyoti
- **Guruh komandiri** “Guruh zalyotlari” (`/mening-guruhim/zalyotlar/`) va “Zalyot kiritish” orqali faqat o‘z guruhining o‘g‘il, faol, naryadga chiqadigan kursantiga zalyot kiritadi.
  - Saqlashdan oldin tasdiqlash sahifasi: “X (BI-525) ga N ta jazo naryadi kiritiladi. Davom etasizmi?”.
  - Zalyot darhol faol bo‘ladi.
- **Cheklovlar** (serverda; Sozlamalarda o‘zgaradi):
  - komandir uchun 1–3 ta jazo naryadi (admin uchun 1–10 qoladi);
  - tanbeh sanasi kelajakda emas va 30 kundan eski emas;
  - bir kunda 5 ta kiritish;
  - boshqa guruh kursanti id’si — 404, service darajasida 403;
  - bir xil kursant + sana + sabab 1 daqiqa ichida takrorlanmaydi.
- Komandir zalyotni tahrirlay va bekor qila olmaydi (403).
- Komandir o‘z guruhining zalyotlarini va hisobini (zalyotchilar, jami / o‘tildi / qoldi) ko‘radi. “Mening guruhim”da belgi: “Zalyotchi: 3 tadan 1 tasi o‘tildi”.
- **`PenaltyEntry`** — har bir kiritish alohida (kim, qachon, nechta); migratsiya 0018 mavjud zalyotlarni to‘ldiradi. `Penalty.reviewed_at` / `reviewed_by`.

### Qo‘shildi — admin
- **Zalyotchiklar ro‘yxati:** “Kim kiritdi” va qachon; komandir kiritgan yozuvlarda “Yangi” belgisi; “Ko‘rib chiqildi” tugmasi (zalyotni o‘zgartirmaydi).
- **Bosh sahifa banneri:** “Komandirlar kiritgan 2 ta yangi zalyot ko‘rib chiqilmagan” va “Ko‘rib chiqildi” tugmasi.
- **Tahrirlash** (`/zalyotchiklar/<id>/tahrirlash/`): sabab, izoh, sana va soni; kursant o‘zgarmaydi. Soni allaqachon o‘tilganidan kam bo‘lmaydi. Jurnalga eski → yangi qiymatlar yoziladi (`penalty_edit`, `penalty_review`).
- **Zalyot hisobi** (`/zalyotchiklar/hisob/`):
  - guruhlar, kursantlar va “kim kiritdi” bo‘yicha jadvallar;
  - davr (tanbeh sanasi) va guruh filtri;
  - Excel: “Guruhlar”, “Kursantlar”, “Kim kiritdi” varaqlari.

### Qo‘shildi — sinov ma’lumotlarini tozalash
- `naryad/cleanup.py`, sahifa `/sozlamalar/tozalash/` (Sozlamalarda havola, faqat admin) va buyruq `python manage.py clear_test_data [--dry-run]`.
  - **Ko‘rib chiqish:** nima o‘chishi (import qilingan / platformada tuzilgan sutkalar), kursantlar bo‘yicha “oldin → keyin”.
  - **Tasdiqlash:** ikki so‘z — “TOZALASH”, so‘ng “HAMMASI NOL”.
  - **Avtomatik zaxira** `zaxira_YYYY-MM-DD_HH-MM-SS.json.gz`: muvaffaqiyatsiz bo‘lsa o‘chirish boshlanmaydi; yuklab olish tugmasi bor.
  - Bitta tranzaksiya; ikkinchi marta o‘chirmaydi. Jurnalda faqat “Sinov ma’lumotlari tozalandi” qoladi.
  - O‘chadi: haftalar, sutkalar, naryadlar, guruh → joy taqsimotlari, e’lon qilingan naryadlar, zalyotlar, jurnal.
  - Qoladi: kursantlar, akkauntlar, sozlamalar, boshlang‘ich taqsimot, sababli holatlar, kasallar.
- Tozalashdan keyin birinchi sutka bo‘sh tarixdan boshlang‘ich taqsimot bo‘yicha tuziladi; test qilingan.
- `scripts/simulate_weeks.py --komandirlar` — 6 ta komandir kiritgan zalyotchi bilan 12 hafta.
- Testlar: `tests/test_commander_penalties.py` (21), `tests/test_clear_data.py` (14); ruxsatlar auditi yangilandi — jami 590. `scripts/screenshots_v21.py`, `docs/skrinshotlar/v1.11/`.

## [1.10.0] — 2026-10-19

19-bosqich: guruh komandiri roli va “Mening guruhim” paneli — faqat ko‘rish (CLAUDE.md 67-band). Algoritm, qoidalar va PDF shakli o‘zgarmagan.

### Qo‘shildi
- **Uchinchi rol `commander` (Guruh komandiri)**, migratsiya 0017. Mavjud foydalanuvchilarga tegilmagan.
  - Akkaunt guruh komandiri lavozimidagi faol kursantga bog‘lanadi. Lavozim “… guruh komandiri” bilan tugashi kerak; o‘rinbosar, starshina, pisar va kaptyorchik mos kelmaydi.
  - Guruh kursantning guruhidan olinadi. Har guruhga bitta faol komandir akkaunti. Noto‘g‘ri kursantga berishda boshqaruv panelida xato chiqadi.
- **Akkauntlar:**
  - `create_cadet_accounts` va boshqaruv panelidagi yangi amal “Akkaunt yaratish (Excel)” guruh komandirlariga rolni avtomatik beradi;
  - Excel’da “Rol” ustuni;
  - foydalanuvchilar ro‘yxatida “Vaqtinchalik parol berish (Excel)” — parolni tiklash, birinchi kirishda almashtirish majburiy.
- **“Mening guruhim”** (`/mening-guruhim/`):
  - faqat o‘z guruhi, familiya bo‘yicha tartib va qidiruv;
  - har kursant uchun navbatdagi va oxirgi tasdiqlangan naryadi;
  - holat: “Hozir naryadda”, “Kasal: 15.10–20.10” yoki “Naryadga chiqmaydi”;
  - jonli sonlar: “Hozir naryadda: 3 kishi”, “Kasal: 1 kishi” (HTMX, 60 soniya);
  - kursant sahifasi — navbatdagi va oxirgi naryadlar;
  - haftalik ko‘rinish: joriy va keyingi hafta jadvali, telefonda qulay;
  - faqat tasdiqlangan sutkalar.
- **Bosh sahifa:** komandirda “Mening naryadim” o‘rnida “Mening guruhim” kartochkasi. Kursant imkoniyatlari saqlanadi: tasdiqlangan naryadlar, PDF, eslatma, “Mening tarixim”.
- **Xavfsizlik:**
  - guruh doirasi bitta joyda (`naryad/group_scope.py`);
  - boshqa guruh kursantining id’si — 404;
  - komandirga hujjat rasmlari, admin sahifalari va barcha o‘zgartiruvchi POST’lar — 403;
  - kasallik tavsifi, hujjat, sabablar, zalyot va lavozim matni ko‘rinmaydi;
  - lavozimdan bo‘shagan komandir “Mening guruhim”ni ko‘rmaydi.
- `tests/test_commander.py` (26 test). Ruxsatlar auditi komandir roli bilan yangilandi, `docs/05-rollar.md` uch ustunli. `scripts/screenshots_v20.py`, `docs/skrinshotlar/v1.10/`.

## [1.9.0] — 2026-10-19

18-bosqich: platforma nomi **E-NARYAD** va kasallik hujjatlari (CLAUDE.md 65- va 66-bandlar). Algoritm, qoidalar va PDF naryad shakli o‘zgarmagan.

### O‘zgardi — platforma nomi
- Yangi nom **E-NARYAD** (tarjima qilinmaydi) bitta joyda: `settings.SITE_NAME`. Shablonlar uni `platform_name` kontekst o‘zgaruvchisidan, 500 sahifasi `{% site_name %}` tegidan oladi.
  - `site_name` nomi ishlatilmadi: Django kirish sahifasi uni o‘zining sayt nomi bilan almashtiradi.
- Nom almashtirilgan joylar:
  - brauzer tab nomi (`… — E-NARYAD`) va yuqori panel;
  - kirish sahifasi va kurs boshlig‘i banneri;
  - 403/404/500 sahifalari;
  - boshqaruv paneli sarlavhalari va ilova nomi;
  - akkauntlar Excel faylining sarlavhasi;
  - README, CLAUDE.md, qo‘llanma, qisqa yo‘riqnoma (PDF qayta yasaldi), CHANGELOG sarlavhasi.
- “2-kurs” nomdan olib tashlandi, lekin “Bojxona instituti · 2-kurs” izohi va haftalarda qoladi.
- PDF naryad shakli o‘zgarmagan. Faqat metama’lumotda `Creator: E-NARYAD`; `Title` avvalgidek.
- Ichki nomlar o‘zgarmagan: `naryad` paketi, migratsiyalar, baza, URL’lar, Docker/Railway.

### Qo‘shildi — kasallik hujjatlari
- `SickDocument` modeli (migratsiya 0016): UUID kalit, tur (kasallik varaqasi / tibbiy punkt ma’lumotnomasi / boshqa), izoh, JPEG rasm va kichik rasm — ma’lumotlar bazasida (`BinaryField`). Ro‘yxat so‘rovlarida baytlar yuklanmaydi (`defer`).
- **Yuklash** (faqat admin):
  - kasallik yozuviga ko‘pi bilan 5 ta rasm, har biri ≤ 8 MB;
  - turi mazmuni bo‘yicha tekshiriladi (Pillow): JPEG, PNG, WEBP; HEIC uchun aniq xabar;
  - EXIF orientatsiya qo‘llanadi, metama’lumot (GPS) o‘chadi, ≤ 2000 px, sifat 85, kichik rasm 360 px;
  - almashtirish va o‘chirish (tasdiq bilan) bor.
- **Jurnal:** `doc_add`, `doc_replace`, `doc_delete` — hujjat turi va yozuv sanalari, rasm mazmuni yozilmaydi. Kasallik yozuvi o‘chirilsa, rasmlari ham o‘chadi (jurnalda soni).
- **Himoyalangan ko‘rish** `/kasal/<id>/hujjat/<UUID>/` (`?kichik=1`):
  - admin va kursantning o‘zi ko‘radi; boshqa kursantga 403, kirmagan odam kirish sahifasiga yo‘naltiriladi;
  - sarlavhalar: `Cache-Control: private, no-store`, `nosniff`, `X-Robots-Tag: noindex`.
- **Interfeys:**
  - Kasallar ro‘yxatida “📎 2 · Hujjatlar” yoki nozik “Hujjat yo‘q” belgisi;
  - yozuv sahifasida galereya (CSS `:target` bilan kattalashtirish, JavaScript yo‘q, CSP o‘zgarmagan) va telefon kamerasidan yuklash (`accept="image/*"`);
  - kursant kartochkasida “Kasallik hujjatlari — Hujjatlaringiz: 2 ta” (faqat ko‘rish, tavsifsiz), bosh sahifadagi kasallik yozuvida havola.
- Ruxsat `documents.own` (kursant — faqat o‘zinikini ko‘rish).
- Testlar: `tests/test_documents.py` (24), `tests/test_branding.py` (7), ruxsatlar auditi yangilandi — jami 519. `scripts/screenshots_v19.py`, `docs/skrinshotlar/v1.9/`.

## [1.8.0] — 2026-10-19

17-bosqich: kasallar ro‘yxati (CLAUDE.md 64-band). Algoritm, dvigatel, PDF shakli va dizayn o‘zgarmagan: kasal kursant mavjud sababli holat (`Absence`, sabab “kasal”) orqali chetlatiladi. 84 sutkalik etalon xesh avvalgidek.

### Qo‘shildi
- **“Kasallar ro‘yxati” bo‘limi** (faqat admin, menyuda “Sababli holatlar” yonida).
  - Jadval ustunlari: F.I.Sh., guruh, kasallik (qisqa tavsif), qachondan beri, muddati, holat (davom etmoqda / tugagan / kelajakda), kim kiritdi va qachon.
  - Filtrlar: “Hozir kasallar” yoki “Hammasi”, guruh bo‘yicha.
  - Qo‘shish formasi: kursantni qidirib tanlash (100 kishidan), tavsif, boshlanish va tugash sanasi — hammasi majburiy. Ustma-ust yozuv kiritilmaydi.
  - Tahrirlash: tavsif va sanalar; boshlangan yozuvda boshlanish sanasi o‘zgarmaydi (36-band).
  - Tugmalar: “Muddatni uzaytirish”, “Sog‘ayib qaytdi” (muddat bugungi sutkada tugaydi), hali boshlanmagan yozuvni o‘chirish.
  - Har amal jurnalga yoziladi: `sick_add`, `sick_edit`, `sick_extend`, `sick_recover`, `sick_delete`.
- `Absence.illness` maydoni (kasallik tavsifi, faqat admin ko‘radi). Migratsiya 0015. Ruxsat `sick.manage` (faqat admin).
- **Kursant bosh sahifasi:** kasallik davrida “Mening navbatdagi naryadim” o‘rnida “Siz kasallar ro‘yxatidasiz: 15.10 dan 20.10 gacha” chiqadi, tavsifsiz. Boshqa kursantlar, sutka sahifasi va PDF’da kasallik belgisi yo‘q.
- **Almashtirish oynasi:** kasal kursantni tanlab bo‘lmaydi, sababi “Kasal: 16.10–19.10 (kasallar ro‘yxatida)” deb ko‘rsatiladi.
- **Qoralamada kasal kursant:** sariq ogohlantirish va shu o‘ringa “Almashtirish” tugmasi. Sutka tasdiqlanmaydi (32-band).
- **Tasdiqlangan sutkaga to‘g‘ri kelgan kasallik:** ro‘yxat o‘zgarmaydi. Kiritishda va sutka sahifasida admin ogohlantiriladi: “… sutkada naryadda, u tasdiqlangan. Almashtirish uchun avval tasdiqni bekor qiling.”
- “Sababli holatlar” sahifasida kasallik yozuvlari tavsifi va “Kasallar ro‘yxatida tahrirlash” havolasi bilan ko‘rinadi.
- `tests/test_sick.py` (20 test) va ruxsatlar auditi yangilandi (jami 484). `scripts/screenshots_v18.py`, `docs/skrinshotlar/v1.8/`.

## [1.7.0] — 2026-10-18

16-bosqich: kursant ko‘rinishi kengaydi, sababli holat eslatmasi, “ozod” yozuvi olib tashlandi (CLAUDE.md 63-band).
Algoritm, generator, PDF shakli va hisoblashlar o‘zgarmagan: 84 sutkalik etalon xesh avvalgidek.

### O‘zgardi
- **Kursant tasdiqlangan ro‘yxatlarni yana ko‘radi** (14-bosqichdagi cheklov bekor qilindi, 60-band):
  - menyuga “Tasdiqlangan naryadlar” qaytdi; ro‘yxatda kursant turgan sutkalar “Siz naryaddasiz” belgisi bilan;
  - sutka sahifasi faqat o‘qish uchun: joylar bo‘yicha guruhlangan (joy, lavozim, F.I.Sh., guruh), kursantning o‘z o‘rni ajratilgan (“Siz”);
  - oldingi/keyingi havolalari faqat tasdiqlangan sutkalarga olib boradi;
  - tasdiqlangan sutka PDF’i va chop etish (o‘zbekcha, shakl o‘zgarmagan); hafta PDF’ida faqat tasdiqlangan sutkalar.
- **Kursantga yopiq (403, serverda tekshiriladi):** qoralama va tuzilmagan sutka sahifasi, qoralama PDF’i va chop etish, jurnal, boshqa kursantlarning kartochkasi, statistika va Excel, sababli holatlar, zalyotchiklar, kursantlar ro‘yxati, haftalar, almashtirish oynasi.
  - Kursant sahifasida tugmalar, “qo‘lda” (✎) belgisi, “Tasdiqlagan” qatori, jurnal havolasi yo‘q.
  - Jazo (zalyot) naryadi oddiy posbon bo‘lib ko‘rinadi.
- **“Ozod” yozuvi olib tashlandi** (uch tilda): guruh jadvallari, statistika, kursantlar ro‘yxati, kartochka, almashtirish oynasi, ogohlantirishlar va xabarlar.
  - Uning o‘rnida lavozim yozuvi: Kurs starshinasi, Guruh komandiri, Kurs pisari, Kaptyorchik.
  - Filtr va ustun “Naryadga chiqmaydi” deb nomlandi (platforma va Django boshqaruv paneli). `?holat=ozod` eski havolalari ishlaydi, yangisi `?holat=lavozimda`.
  - `duty_exempt`, generator qoidalari va hisoblashlar o‘zgarmagan. Migratsiya 0014 faqat maydon nomini o‘zgartiradi, SQL o‘zgarishi yo‘q.
  - Jurnaldagi eski yozuvlar o‘zgarmagan.

### Qo‘shildi
- `templates/partials/duty_reason_notice.html`: qayta ishlatiladigan sababli holat eslatmasi (sariq blok, uch tilda). U kursant bosh sahifasida, “Tasdiqlangan naryadlar” va sutka sahifasida chiqadi, admin sahifalarida yo‘q. Keyingi bosqichda guruh komandiri paneliga ham qo‘yiladi.
- `tests/test_cadet_roster.py` (14 test), ruxsatlar auditi va mavjud testlar 16-bosqichga moslandi (jami 464).
- `scripts/screenshots_v17.py`, `docs/skrinshotlar/v1.7/`.

## [1.6.1] — 2026-10-15

1.6.0 ochiq savollari bo‘yicha qarorlar (CLAUDE.md 62-band).

### O‘zgardi
- Faol zalyoti bor kursantni naryaddan ozod qilib bo‘lmaydi: kartochkada sababi ko‘rsatiladi, ozod qilish formasi chiqmaydi.
- Bekor qilingan zalyotning kursanti qoralamada jazo o‘rnida qolsa, sutka tasdiqlanmaydi (avval faqat eslatma edi).
- Qolgan ikki qaror o‘zgarishsiz tasdiqlandi:
  - kursant bosh sahifasidagi sonlar faqat oddiy naryadlarni sanaydi;
  - oddiy navbatdagi farqni algoritm keyin o‘zi tenglashtiradi.
- 2 ta yangi test (jami 450).

## [1.6.0] — 2026-10-15

15-bosqich: zalyotchiklar — navbatdan tashqari jazo naryadi (CLAUDE.md 61-band). PDF shakli o‘zgarmagan.
Zalyotchik bo‘lmasa, generator natijasi bayt-bayt avvalgidek: 84 sutkalik etalon xesh, 3 stsenariyli barmoq izi va 12 haftalik simulyatsiya v1.5.0 bilan bir xil.

### Qo‘shildi
- **`Penalty` (zalyot) modeli:** kursant, sabab turi, izoh, buyruq/tanbeh sanasi, jazo naryadlari soni, holat (faol / bajarildi / bekor qilindi), kim kiritgan va qachon.
  - Bir kursantda bitta faol zalyot; yangisi qo‘shilsa, soni mavjudiga qo‘shiladi.
  - Har amal jurnalga yoziladi.
  - Faqat o‘g‘il, faol, naryaddan ozod bo‘lmagan kursant.
- **Dvigatel** (`place_offenders`, `generate_day(offenders=…)`):
  - faol zalyotchik faqat 1-NO‘J yoki 1-Yotoqxonaga, posbon o‘rniga, oddiy to‘ldirishdan OLDIN qo‘yiladi; shu joy guruhi bitta kam beradi;
  - bir joyga ko‘pi bilan 1 ta (Sozlamalarda 2 qilish mumkin), tanbeh sanasi eskisi birinchi, joy navbatma-navbat;
  - kecha turgan va sababli holatdagi zalyotchik qo‘yilmaydi — ogohlantirish chiqadi; o‘rin qolmasa, keyingi sutkaga qoladi;
  - faol zalyotchik oddiy navbatda boshqa joylarga tushmaydi.
- **Hisob:**
  - `Assignment.kind` (normal / penalty) va `Assignment.penalty`. Migratsiya 0013 mavjud yozuvlarni `normal` qiladi.
  - Jazo naryadi faqat sutka tasdiqlanganda “o‘tildi” sanaladi; tasdiq bekor qilinsa, hisob qaytadi. Soni tugagach zalyot “bajarildi” bo‘ladi.
- **“Zalyotchiklar” sahifasi** (`/zalyotchiklar/`, faqat admin):
  - faol va yakunlangan zalyotlar (jami / o‘tildi / qoldi);
  - kiritish formasi, sabab bilan bekor qilish;
  - har zalyotning sutkalari havolasi.
- **Sutka sahifasi:**
  - jazo o‘rni “Zalyot” belgisi bilan;
  - qo‘yilmagan zalyotchiklar haqida sariq eslatma, joriy tilda;
  - tasdiqlashga to‘sqinlik qilmaydigan eslatmalar alohida chiqadi.
- **Almashtirish:**
  - jazo o‘rniga faqat boshqa faol zalyotchik yoki shu joy guruhi kursanti qo‘yiladi;
  - faol zalyotchikni boshqa joylarga qo‘yib bo‘lmaydi;
  - jazo o‘rnidagi zalyotchikning lavozimi almashtirilmaydi.
- **Kursant ko‘rinishi:**
  - admin uchun kursant kartochkasida “Zalyot tarixi”;
  - kursant bosh sahifasida “Navbatdan tashqari naryad” va “Jazo naryadlari: 3 tadan 1 tasi o‘tildi”.
- **Statistika:** “Jazo naryadlari” ustuni; Excel’da shu ustun va “Zalyotchiklar” varag‘i.
- **Simulyatsiya:** `scripts/simulate_weeks.py --zalyotchiklar` — 12 hafta, 3 ta zalyotchik va natija jadvali.
- **Testlar:** `tests/test_penalties.py` (20 ta). Ruxsatlar auditi yangilandi. `scripts/screenshots_v16.py` → `docs/skrinshotlar/v1.6/`.
- **Tarjimalar:** yangi matnlar uch tilda; `docs/atamalar.md` ga zalyotchik atamalari qo‘shildi.

### O‘zgardi
- Adolat hisobi faqat oddiy naryadlarni sanaydi: statistika, nishonlar, saralash kaliti, guruhlar aylanishi, kursant kartochkasidagi sonlar.
- Sozlamalarda yangi maydon: “bir joyga zalyotchiklar (sutkada)”.
- Boshqaruv panelida zalyotlar faqat ko‘rish uchun.

## [1.5.0] — 2026-10-15

14-bosqich: kursant ko‘rinishi va ertangi ro‘yxatni oldindan tayyorlash. Algoritm, qoidalar va PDF shakli o‘zgarmagan (CLAUDE.md 60-band).

### Qo‘shildi
- **“Mening navbatdagi naryadim”** — kursant bosh sahifasida katta kartochka:
  - sana va vaqt (“15-oktabr, chorshanba 18:00 → 16-oktabr 18:00”);
  - joy va lavozim yirik yozuvda, guruh;
  - jonli hisoblagich: “Naryadga 21 soat 14 daqiqa qoldi”, naryad davomida “Hozir naryaddasiz, smena almashishiga … qoldi”. Server vaqti asosida ishlaydi, naryad boshlanganda yoki tugaganda kartochka o‘zi yangilanadi;
  - naryad bo‘lmasa: “Yaqin kunlarda tasdiqlangan naryadingiz yo‘q”.
- **“Naryadingiz bekor qilindi”:**
  - sutka tasdiqlanganda kursantlar `PublishedDuty` ga yoziladi;
  - tasdiq bekor qilinib kursant almashtirilsa, unga sababsiz shu xabar chiqadi;
  - yangi kursant naryadni sutka qayta tasdiqlangach ko‘radi.
- **Tayyorgarlik eslatmasi** (`PrepNote`):
  - Sozlamalar sahifasida har joy uchun uch tilda kiritiladi;
  - kursant o‘z joyinikini kartochkada ko‘radi;
  - bo‘sh bo‘lsa ko‘rsatilmaydi.
- **Ertangi ro‘yxat muddati:** D sanadagi sutka D−1 kuni 18:00 gacha tasdiqlangan bo‘lishi kerak.
  - Muddat `Setting.approval_lead_hours` da, standart 24 soat.
  - Admin bosh sahifasida banner:
    - sariq — qolgan vaqt va “Tuzish”/“Ochish” tugmasi;
    - qizil — “Muddat o‘tdi, kursantlar hali bilmaydi”;
    - yashil — “Ertangi ro‘yxat tayyor, kursantlarga ko‘rinmoqda”.
  - Banner faqat 2-kurs haftasi kunlarida va hafta oldidan shanba kuni ko‘rinadi.
- **Migratsiya 0012:** muddat sozlamasi, `PrepNote`, `PublishedDuty`. Hozir tasdiqlangan sutkalardagi kursantlar e’lon qilingan deb belgilanadi.
- **Testlar:** `tests/test_cadet_view.py` (29 ta) — vaqt “muzlatilgan”:
  - kartochka;
  - hisoblagich;
  - qoralama ko‘rinmasligi;
  - 403 sahifalar;
  - bekor qilish;
  - eslatma;
  - banner (sariq, qizil, yashil, hafta tashqarisi, sozlama);
  - uch til.
- **Skrinshotlar:** `scripts/screenshots_v15.py` → `docs/skrinshotlar/v1.5/`.
- **Tarjimalar:** yangi matnlar uch tilda, `docs/atamalar.md` ga yangi atamalar qo‘shildi.

### O‘zgardi
- **Kursant boshqa kursantlarning ro‘yxatini ko‘rmaydi.**
  - Menyudan “Tasdiqlangan naryadlar” olib tashlandi.
  - Sutka sahifalari, sutka va hafta PDF’i, chop etish va boshqa kursantlarning kartochkalari kursantga 403 qaytaradi (`day.view_approved`, `pdf.export` — faqat admin, `docs/05-rollar.md`).
  - Bosh sahifadan “Oxirgi naryadlar” ro‘yxati olib tashlandi; to‘liq tarix “Mening tarixim”da.
- **Admin bosh sahifasidagi SQL so‘rovlar chegarasi** 15 dan 18 ga ko‘tarildi (banner uchun).

### Tuzatildi
- Tasdiqlovchisi yo‘q sutka sahifasi va foydalanuvchisi yo‘q jurnal yozuvi xato bermaydi. Masalan, import qilingan tarix sutkalari.

## [1.4.0] — 2026-10-14

13-bosqich: uch til — o‘zbekcha (asosiy), ruscha, inglizcha. Algoritm, qoidalar, PDF shakli va dizayn o‘zgarmagan (CLAUDE.md 59-band).

### Qo‘shildi
- **Til tanlash:** sarlavhada tungi rejim tugmasi yonida va kirish sahifasida `UZ | RU | EN` tugmalari bor.
  - POST + CSRF bilan ishlaydi va o‘sha sahifaga qaytaradi.
  - Telefonda tugmalar sarlavhaning ikkinchi qatoriga tushadi.
- **Tanlov saqlanishi:**
  - kirgan foydalanuvchida — `User.language` (migratsiya 0011), shuning uchun boshqa qurilmada ham shu til ochiladi;
  - kirmaganda — `naryad_til` cookie’si;
  - kirish sahifasida tanlangan til kirgach akkauntga yoziladi.
- **Asosiy til:** sukut bo‘yicha doim o‘zbekcha, brauzer tili (`Accept-Language`) hisobga olinmaydi. URL’da til prefiksi yo‘q.
- **Middleware:** `naryad/i18n.py` — Django’ning `LocaleMiddleware` o‘rnida `LanguageMiddleware`, hamda `set_language`.
- **Sana formatlari:** “14-oktabr 2026” / “14 октября 2026” / “14 October 2026”. Hafta kunlari va oylar har tilda.
- **JavaScript (soat, “Smena almashishiga … qoldi”, rejim nomlari):** matnlar serverdan `data-` atributlari orqali tanlangan tilda keladi. CSP o‘zgarmagan.
- **Tarjimalar:** `locale/ru` va `locale/en` da 677 tadan yozuv; hammasi to‘ldirilgan, `fuzzy` yo‘q, `.mo` kompilyatsiya qilingan.
  - Ruscha — 4 ta ko‘plik shakli (`blocktranslate count` / `ngettext`).
  - Tarjima qilinganlar: shablonlar, model nomlari va tanlovlar, formalar va xatolar, xabarlar, ogohlantirishlar, menyu, statistika, 403/404/500, admin panel.
- **Bazadagi doimiy nomlar** (joylar, PDF qatorlari, yo‘nalishlar) va algoritmning chetlatish sabablari `naryad/i18n_data.py` da. Ular ko‘rsatishda tarjima qilinadi.
- **Atamalar lug‘ati:** `docs/atamalar.md` (o‘zbek — rus — ingliz).
- **`makemessages` buyrug‘i** `_lazy` taxallusini ham taniydi (`naryad/management/commands/makemessages.py`).
- **Testlar:** `tests/test_i18n.py` (26 ta):
  - har sahifa uch tilda to‘g‘ri `<html lang>` bilan ochiladi;
  - ruscha/inglizcha sahifalarda o‘zbekcha so‘z qolmagan;
  - `.po` to‘liq, bo‘sh/`fuzzy` yo‘q;
  - `Accept-Language: ru` → o‘zbekcha;
  - tanlov chiqib-kirgandan keyin va boshqa qurilmada saqlanadi;
  - inglizcha sessiyada ham PDF va Excel o‘zbekcha;
  - sana formatlari.
- **Skrinshotlar:** `scripts/screenshots_v14.py` → `docs/skrinshotlar/v1.4/`. `scripts/ui_audit.py` da `LANG_CODE=uz|ru|en`.

### O‘zgarmaydi (tarjima qilinmaydi)
- PDF naryad shakli — doim o‘zbekcha (`translation.override("uz")`).
- Excel eksport ustun nomlari.
- Kursant F.I.Sh., guruh kodlari, admin yozgan sabab va izohlar.
- Jurnal va sabablar har doim o‘zbekcha saqlanadi va ko‘rsatiladi.

### Tuzatildi
- Boshqaruv panelidagi kursantlar ro‘yxatida “F.I.Sh.” ustuni inglizcha “Full name” bo‘lib chiqardi.
- Skrinshot va audit skriptlari kirish tugmasini aniq tanlaydi (til tugmalari ham `submit`).

## [1.3.0] — 2026-10-14

12-bosqich — dizayn: institut rasmi, emblema, jonli bosh sahifa, tungi rejim. Algoritm, qoidalar va PDF shakli o‘zgarmagan.
11-bosqich (1.2.0) hali qilinmagan; bu versiya 1.1.0 ustiga qurilgan.

### Qo‘shildi
- **Rasmlar** (`scripts/prepare_images.py`, Pillow, deterministik). Asl fayllar `assets/` da.
  - Institut binosi 16:9 ga kesilgan: 1920 va 960 px, webp + jpg, sifat 78–80, har biri ≤ 300 KB.
  - Emblema qora fonsiz (shaffof): 512 / 192 / 64 px.
  - `favicon.ico`, `apple-touch-icon.png`.
- **Rang:** asosiy rang **to‘q ko‘k** (`brand`), aksent — emblemadagi oltin (`gold`). Ikkalasi Tailwind config’da nom bilan. Holat belgilari (tasdiqlangan, yashil/sariq/qizil adolat) avvalgidek.
- **Sarlavhada emblema;** kirish sahifasi institut rasmi fonida, to‘q ko‘k qatlam bilan, markazda emblema va kartochka.
- **Bosh sahifa banneri** (admin va kursant):
  - institut rasmi va pastga qorayib boruvchi gradient;
  - emblema va sarlavha;
  - kartochkalar rasm ustiga yarim chiqib turadi (`bg-white/85 backdrop-blur`).
- **Jonli soat** — Toshkent vaqti, o‘zbekcha hafta kuni va sana. Server vaqtidan olinadi (`data-server-now`), telefon soatiga bog‘liq emas.
- **Joriy sutka paneli** — progress chizig‘i va “Smena almashishiga … qoldi”. 18:00 da sahifani yangilamasdan keyingi sutkaga o‘tadi.
- **Bosh sahifa holat kartochkalari** har 60 soniyada HTMX bilan yangilanadi (`/bosh-sahifa/holat/`). Yashirin tabda so‘rov yuborilmaydi.
- **Tungi rejim** (`darkMode: "class"`):
  - sarlavhada tugma: avtomatik → kunduzgi → tungi;
  - tanlov `localStorage` da saqlanadi;
  - `static/js/theme.js` `<head>` da yuklanadi, shuning uchun oq “yaltirash” bo‘lmaydi;
  - tungi ranglar `static/src/input.css` da markazlashgan.
- **Testlar:** `tests/test_design.py` (20 ta). `scripts/ui_audit.py` da `THEME=dark`. `scripts/screenshots_v13.py` → `docs/skrinshotlar/v1.3/`.
- **Versiya** sahifa pastida ko‘rsatiladi.

### O‘zgardi
- Statistika issiqlik xaritasi to‘q ko‘k tusda.
- Kompyuter menyusi 1024 px dan boshlab ko‘rinadi. Undan torroq ekranda “Menyu” tugmasi chiqadi.
- Telefonda guruh kodlari bo‘linmaydi.
- Content-Security-Policy o‘zgarmagan. Inline skript yo‘q, rasmlar faqat o‘z serverimizdan.

## [1.1.0] — 2026-10-13

### Qo‘shildi — naryaddan ozod kursantlar (komandirlar va kurs lavozimlari)
- `Cadet.duty_exempt` va `duty_position` (`is_active` dan alohida). Jurnalga ikki yangi amal yoziladi: “Naryaddan ozod qilindi” va “Naryadga qaytarildi” (sabab majburiy).
- Migratsiya 0010 belgilaydi 9 kishini:
  - kurs starshinasi, kurs pisari, kaptyorchik va 6 guruh komandiri;
  - guruh + to‘liq F.I.Sh. bo‘yicha aniq topiladi, topilmasa migratsiya to‘xtaydi.
- `data/roster.json` va `load_roster` da yangi maydonlar. Naryadga chiqadiganlar: 11 / 12 / 12 / 14 / 16 / 13 (jami 78).
- Generator, almashtirish oynasi va tasdiqlash: ozod kursant tanlanmaydi, qo‘lda qo‘yib bo‘lmaydi (sababi ko‘rsatiladi). Qoralamada bo‘lsa — qizil ogohlantirish, tasdiqlab bo‘lmaydi.
- Kursantlar sahifasi:
  - “ozod” belgisi va filtr;
  - “Naryadga chiqadi” ustuni;
  - kartochkada ozod qilish / naryadga qaytarish.
- Statistika: adolat hisobi va “bir o‘g‘ilga o‘rtacha” faqat naryadga chiqadiganlar bo‘yicha; Excel’da “Naryaddan ozod” ustuni.

## [1.0.0] — 2026-10-13

Birinchi to‘liq versiya: 2-kurs sutkalik naryadini tarix asosida, adolatli va avtomatik tuzish, tasdiqlash, PDF, statistika, serverga joylash.

### 10-bosqich — sayqal, xavfsizlik, zaxira, joylashtirish
**Qo‘shildi**
- Production sozlamalari (`config/settings_prod.py`): HTTPS majburiy, xavfsiz cookie, HSTS, CSP, `X-Frame-Options`. `check --deploy` — 0 ogohlantirish.
- `docker-compose.prod.yml`: web (gunicorn), PostgreSQL, Caddy (avtomatik HTTPS), kunlik zaxira. Har servisda healthcheck, loglar hajmi cheklangan.
- `/health/` manzili (baza ulanishi bilan).
- `scripts/backup.sh` (har kuni, 30 kun) va `scripts/restore.sh` (xavfsizlik zaxirasi bilan). Tiklash sinab ko‘rildi.
- Hujjatlar:
  - `docs/joylashtirish.md` — VPS, internetsiz ichki tarmoq, Railway, yangilash, tiklash;
  - `docs/qollanma.md` — skrinshotlar bilan;
  - bir sahifalik `docs/qollanma/qisqa-yoriqnoma.pdf`;
  - `docs/xavfsizlik.md`.
- Testlar:
  - har bir URL × rol bo‘yicha ruxsatlar auditi;
  - xavfsizlik sarlavhalari, yuklash cheklovlari;
  - SQL so‘rovlar soni chegarasi.
- Qizlar statistikasida “ketma-ket ikki marta navbatchi” holatlari.
- O‘zbekcha 404 va 500 sahifalari; admin panelda “Platformaga qaytish” havolasi.
- `scripts/ui_audit.py` — 360/1280 px interfeys auditi. `scripts/screenshots_manual.py` — production’dagi to‘liq oqim va qo‘llanma rasmlari.

**O‘zgardi**
- Barcha inline JavaScript `static/js/app.js` va `print.js` ga ko‘chirildi (CSP `script-src 'self'`).
- Tugma va havolalar kamida 44 px; matnlar telefonda kesilmaydi; eski haftalar yig‘ilgan holda.
- Kursantlar Excel importi: ZIP tuzilmasi, ochilgandagi hajm va qatorlar soni tekshiriladi.
- N+1 tuzatildi (so‘rovlar soni):

  | Sahifa | Oldin | Keyin |
  |---|---|---|
  | Bosh sahifa | 27 | 10 |
  | Kursantlar | 23 | 6 |
  | Statistika | 53 | 19 |
  | Excel | 67 | 18 |

- Admin panel: ishlatilmaydigan “Guruhlar (huquqlar)” olib tashlandi; tarjimalardagi apostroflar ‘/’ ga keltirildi.
- WeasyPrint/fontTools INFO loglari o‘chirildi.

### 9-bosqich — statistika va adolat ko‘rsatkichi
- Statistika sahifasi:
  - davr filtri;
  - kursant × joy/lavozim issiqlik xaritasi;
  - qizlar alohida;
  - adolat belgisi (yashil ≤ 1, sariq = 2, qizil ≥ 3) va ketma-ket bir joy holatlari;
  - guruhlar kesimi;
  - qo‘lda tuzatishlar nazorati va ogohlantirish.
- Excel eksport (har jadval alohida varaqda), kursant kartochkasida guruh o‘rtachasi bilan solishtirish, bosh sahifada adolat belgilari.
- `ChangeLog.reason_code`, 12 haftalik simulyatsiya skripti.

### 8-bosqich — PDF
- Rasmiy shakldagi A4 PDF (WeasyPrint, Times New Roman / Liberation Serif), hafta PDF’i, chop etish sahifasi.
- Qoralama PDF’ida “QORALAMA” yozuvi.
- Qoralamani o‘chirish (sabab bilan).

### 7-bosqich — naryad generatori
- 2-kurs haftasini ochish, sutkama-sutka qoralama tuzish.
- Almashtirish va lavozimlarni almashtirish (sabab majburiy).
- Tasdiqlash va qayta ochish, jurnal, sababli holatlar.
- Bir vaqtda tahrirlashdan himoya.

### 6-bosqich — kursantlar bazasi
- Ro‘yxat, qidiruv, filtrlar; qo‘shish, tahrirlash, faolsizlantirish; Excel import (ko‘rib chiqish → tasdiqlash); kursant kartochkasi.

### 5-bosqich — kirish, rollar, interfeys
- Kirish (login cheklovi bilan), majburiy parol almashtirish.
- Ikki rol (admin, kursant) va ruxsatlar jadvali.
- Tailwind (Node’siz) va HTMX asosidagi telefonbop interfeys; o‘zbekcha tarjimalar.

### 4-bosqich — boshlang‘ich ma’lumotlar
- `load_roster` (100 kursant, 6 guruh), `import_history` (o‘tgan sutkalar), `create_cadet_accounts`.
- Boshlang‘ich guruh → joy taqsimoti.

### 3-bosqich — Django skeleti
- Modellar, migratsiyalar, admin panel, services qatlami, Docker va docker-compose.

### 2-bosqich — taqsimlash algoritmi
- Frameworkdan mustaqil `naryad/engine/`: guruhlar aylanishi, adolatli tanlash, lavozimlarni taqsimlash, testlar va namunaviy hisob.

### 1-bosqich — talablar va sxema
- Talablar, texnologiyalar steki, ma’lumotlar bazasi sxemasi (`docs/01-talablar-va-sxema.md`).
