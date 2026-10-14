# O‘zgarishlar tarixi

Format: [Keep a Changelog](https://keepachangelog.com/), versiyalar: [SemVer](https://semver.org/).

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
