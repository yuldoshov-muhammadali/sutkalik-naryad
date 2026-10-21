# E-NARYAD — 2-kurs sutkalik naryad platformasi

**E-NARYAD** — Bojxona instituti 2-kurs kursantlari uchun sutkalik naryadni tarix asosida, adolatli va avtomatik tuzuvchi veb-platforma.
Loyiha qoidalari: [`CLAUDE.md`](CLAUDE.md). Talablar va sxema: [`docs/01-talablar-va-sxema.md`](docs/01-talablar-va-sxema.md). Algoritm: [`docs/02-algoritm.md`](docs/02-algoritm.md).

| Kim uchun | Hujjat |
|---|---|
| Foydalanuvchilar (kurs boshlig‘i, kursant) | [`docs/qollanma.md`](docs/qollanma.md), bir sahifalik: [`docs/qollanma/qisqa-yoriqnoma.pdf`](docs/qollanma/qisqa-yoriqnoma.pdf) |
| Serverga joylash, yangilash, zaxira | [`docs/joylashtirish.md`](docs/joylashtirish.md) |
| Xavfsizlik | [`docs/xavfsizlik.md`](docs/xavfsizlik.md) |
| O‘zgarishlar tarixi | [`CHANGELOG.md`](CHANGELOG.md) — joriy versiya **1.6.1** |

## Tuzilishi

```
config/              Django sozlamalari (settings.py, settings_test.py, urls.py)
naryad/              asosiy ilova: models.py, admin.py, services.py, migrations/
naryad/engine/       frameworkdan mustaqil taqsimlash algoritmi (faqat standart kutubxona)
scripts/             build_roster.py (.doc → roster.json), demo.py (namunaviy hisob),
                     make_history_templates.py (tarix shablonlari)
naryad/importers.py  load_roster va import_history mantig'i
naryad/management/   manage.py buyruqlari: load_roster, import_history, create_cadet_accounts
naryad/permissions.py rollar va ruxsatlar jadvali (docs/05-rollar.md)
naryad/cadets.py, cadet_import.py, views_cadets.py  kursantlar bazasi (6-bosqich)
naryad/days.py, absences.py, views_days.py  haftalar, sutka, tuzatish, tasdiqlash, sababli holatlar (7-bosqich)
naryad/pdf.py, templates/naryad/pdf/  rasmiy shakldagi PDF (8-bosqich); fonts/ — Times New Roman (o'zingiz qo'yasiz)
naryad/stats.py, views_stats.py  statistika, adolat ko'rsatkichi, Excel eksport (9-bosqich)
naryad/security.py   /health/ va Content-Security-Policy; config/settings_prod.py — production (10-bosqich)
docker-compose.prod.yml, docker/Caddyfile  server: web + PostgreSQL + Caddy (HTTPS) + kunlik zaxira
scripts/backup.sh, restore.sh  zaxira olish va tiklash
templates/, static/  shablonlar, Tailwind CSS (tayyor), HTMX
locale/uz/           admin/auth uchun o'zbekcha tarjimalar
data/                2-KURS ROYXATI.doc, roster.json, tarix_shablon.xlsx, tarix_namuna.xlsx
tests/               pytest testlari (algoritm, modellar, services, admin, interfeys, kursantlar, sutka, PDF, statistika,
                     xavfsizlik va ruxsatlar auditi, SQL so'rovlar soni)
docker/entrypoint.sh migratsiya + gunicorn
```

## Birinchi ishga tushirish

Har qanday muhitda (lokal yoki Docker) bir marta bajariladi:

```bash
python manage.py migrate                 # jadvallar, 7 joy / 20 o'rin, standart sozlamalar
python manage.py createsuperuser         # kurs boshlig'i (admin roli avtomatik)
python manage.py load_roster             # 6 guruh va 100 kursant (data/roster.json, 9 ta naryaddan ozod) — faqat birinchi marta!
```

So‘ng **bittasini** tanlang:

- **O‘tgan (qog‘ozdagi) sutkalar bo‘lsa** — `data/tarix_shablon.xlsx` ni to‘ldiring (namuna: `data/tarix_namuna.xlsx`, 18-sentabr) va import qiling:

  ```bash
  python manage.py import_history tarix.xlsx --dry-run   # avval tekshirish, bazaga yozilmaydi
  python manage.py import_history tarix.xlsx             # yozish
  ```

  Bitta ham xato bo‘lsa hech narsa yozilmaydi; xatolar qator raqami bilan chiqadi. Kerakli 2-kurs haftasi avtomatik ochiladi.

- **Tarix bo‘lmasa** — admin panel → *Sozlamalar* → *Boshlang‘ich guruh → joy taqsimoti*: 6 ta joyning har biriga bitta guruh. Birinchi sutka shu taqsimot bilan tuziladi, keyin zanjir avtomatik davom etadi.

> **`load_roster` faqat birinchi ishga tushirishda ishlatiladi.** Keyin kursantlar admin panelda tahrirlanadi: buyruq qayta ishga tushirilsa, admin kiritgan tuzatishlarni `roster.json` dagi holatga qaytaradi.

Kursantlarga akkaunt berish (login `familiya.ism`, vaqtinchalik parol, birinchi kirishda almashtiriladi):

```bash
python manage.py create_cadet_accounts   # data/akkauntlar_<sana>.xlsx — chop eting, keyin faylni o'chiring
```

Qayta ishga tushirilsa, faqat akkaunti yo‘q (yangi) kursantlarga akkaunt yaratadi.

Docker’da buyruqlar oldiga `docker compose exec web` qo‘shiladi, masalan: `docker compose exec web python manage.py load_roster`. Import faylini avval konteynerga nusxalang: `docker compose cp tarix.xlsx web:/app/tarix.xlsx`.

Platforma: `http://127.0.0.1:8000/` (kirish — `/kirish/`). Kursantlar bazasi (admin): `/kursantlar/` — ro‘yxat, qo‘shish, tahrirlash, faolsizlantirish, Excel import (`/kursantlar/import/`, shablon shu sahifada). Kursant o‘z tarixini `/mening-tarixim/` da ko‘radi.

Naryad oqimi (admin): **Haftalar** (`/haftalar/`) → yakshanbani tanlab haftani ochish → sutka sahifasi (`/sutka/2026-09-19/`) → **Tuzish** → kerak bo‘lsa **Almashtirish** / **Lavozimlarni almashtirish** (sabab majburiy) → **Tasdiqlash**. Sababli holatlar: `/sababli/`. Sutka jurnali: `/sutka/<sana>/jurnal/`. Kursantlar tasdiqlangan sutkalarni `/sutkalar/` da ko‘radi.

Boshqaruv paneli `/admin/` — faqat **admin roli** va superuser. Rollar va ruxsatlar: [`docs/05-rollar.md`](docs/05-rollar.md).

## Statistika va adolat (9-bosqich)

- `/statistika/` (faqat admin): davr (butun tarix / sanadan sanagacha / bitta 2-kurs haftasi), guruh tanlanadi. Kursant × joy va lavozimlar jadvali (issiqlik xaritasi), qizlar alohida, adolat belgisi (yashil ≤ 1, sariq = 2, qizil ≥ 3), ketma-ket bir joy holatlari, guruhlar kesimi, qo‘lda tuzatishlar nazorati.
- **Excel’ga yuklab olish** — barcha jadvallar bitta `.xlsx` da, har biri alohida varaqda, tanlangan davr bilan.
- Bosh sahifada har guruhning adolat belgisi; kursant o‘z kartochkasida o‘zini guruh o‘rtachasi bilan solishtiradi (boshqalarning ismisiz).
- Hammasi faqat **tasdiqlangan** sutkalardan, so‘rov paytida hisoblanadi.
- Sinab ko‘rish uchun 12 haftalik simulyatsiya (**faqat alohida bazada!**):

  ```bash
  DATABASE_URL=sqlite:///simulyatsiya.sqlite3 python scripts/simulate_weeks.py
  DATABASE_URL=sqlite:///simulyatsiya.sqlite3 python manage.py runserver   # kursboshligi / Demo-parol-2026
  ```
  `--zalyotchiklar` qo‘shilsa, 3-hafta boshida 3 ta zalyotchik (2–3 tadan jazo naryadi) kiritiladi. Oxirida natija jadvali chiqadi: jazo naryadlari qayerda bo‘lgani va guruhlar adolati (15-bosqich).

## Lokal ishga tushirish (Docker’siz, SQLite)

Python 3.12 kerak.

**Linux / macOS:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env              # DJANGO_DEBUG=True qoldiring
python manage.py migrate
python manage.py createsuperuser  # kurs boshlig'i (admin roli avtomatik beriladi)
python manage.py runserver        # http://127.0.0.1:8000/admin/
```

**Windows (PowerShell):**

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1        # cmd.exe da: .venv\Scripts\activate.bat
pip install -r requirements-dev.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> PowerShell skript bajarishni taqiqlasa: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Docker bilan (web + PostgreSQL)

Docker Desktop (Windows/macOS) yoki Docker Engine (Linux) kerak. Buyruqlar hamma tizimda bir xil:

```bash
docker compose up --build -d                              # http://localhost:8000/admin/
docker compose exec web python manage.py createsuperuser
docker compose logs -f web                                # loglar
docker compose down                                       # to'xtatish (ma'lumotlar pgdata volume'da qoladi)
```

Migratsiyalar konteyner ishga tushganda avtomatik bajariladi (`docker/entrypoint.sh`).

## Testlar

```bash
pytest                                          # SQLite
DATABASE_URL=postgres://user:pass@localhost:5432/naryad pytest   # PostgreSQL bilan (ixtiyoriy)
python scripts/demo.py                          # algoritmning namunaviy hisobi
```

## Interfeys (CSS, HTMX, tarjimalar)

- **Tailwind CSS** Node.js’siz, standalone CLI bilan yig‘iladi; tayyor fayl `static/css/app.css` repozitoriyda. Shablon o‘zgarsa:
  ```bash
  curl -sSLo tailwindcss https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 && chmod +x tailwindcss
  sh scripts/build_css.sh        # Windows: tailwindcss-windows-x64.exe -c tailwind.config.js -i static/src/input.css -o static/css/app.css --minify
  ```
- **HTMX** 2.0.4: `static/js/htmx-2.0.4.min.js` (CDN’siz).
- **Rasmlar** (12-bosqich): asl fayllar `assets/institut.jpg`, `assets/emblema.jpg`. Ularni almashtirsangiz: `python scripts/prepare_images.py` (Pillow). Natija `static/img/` ga yoziladi.
- **Ranglar:** `tailwind.config.js` da `brand` (to‘q ko‘k) va `gold`.
- **Tungi rejim:** `darkMode: "class"`. Tungi ranglar `static/src/input.css` da, tanlov `static/js/theme.js` va `app.js` da.
- **Uch til** (13-bosqich): o‘zbekcha (asosiy), ruscha, inglizcha — CLAUDE.md 59-band, atamalar: [`docs/atamalar.md`](docs/atamalar.md).
  - Tarjimalar `locale/ru/LC_MESSAGES/django.po` va `locale/en/LC_MESSAGES/django.po` da. Django admin/auth uchun yetishmagan o‘zbekcha matnlar `locale/uz/LC_MESSAGES/django.po` da.
  - msgid — o‘zbekcha matnning o‘zi. Python’da `gettext as _` va `gettext_lazy as _lazy`, shablonlarda `{% translate %}` / `{% blocktranslate %}`.
  - Yangi matn qo‘shilgach katalogni yangilang. Loyihaning `makemessages` buyrug‘i `_lazy` ni ham taniydi; GNU gettext kerak:
    ```bash
    python manage.py makemessages -l ru -l en --no-obsolete --no-location -i "tests/*" -i "scripts/*" -i "naryad/engine/*" \
      -i "naryad/migrations/*" -i "docs/*" -i "staticfiles/*" -i "assets/*" -i "templates/naryad/pdf/*"
    ```
  - `.po` dagi yangi (bo‘sh yoki `fuzzy`) yozuvlarni tarjima qilgach: `python scripts/compile_messages.py` (`.mo` fayllar ham repozitoriyda). `tests/test_i18n.py` bo‘sh/fuzzy yozuv qolsa yiqiladi.
- **Skrinshotlar** (telefon 390 px va kompyuter 1280 px): [`docs/skrinshotlar/`](docs/skrinshotlar/), qo‘llanma rasmlari: [`docs/qollanma/rasmlar/`](docs/qollanma/rasmlar/) (`scripts/screenshots_manual.py`).
- **Interfeys auditi:** `python scripts/ui_audit.py http://127.0.0.1:8123 audit/` — har sahifani 360 px va 1280 px’da tekshiradi: gorizontal toshish, 44 px dan kichik tugma, inglizcha matn, CSP xatolari.
- **JavaScript** faqat `static/js/` dagi fayllarda (inline skript yo‘q — Content-Security-Policy).

## PDF (rasmiy shakl)

- Sutka sahifasida **PDF yuklab olish** va **Chop etish** tugmalari; haftalar sahifasida **Hafta PDF** (7 sutka, har biri alohida sahifada).
- Fayl nomlari: `naryad_2026-09-18.pdf`, `naryad_hafta_2026-09-13.pdf`. Qoralama PDF’ida “QORALAMA” yozuvi bo‘ladi (faqat admin).
- **Times New Roman** litsenziyali, shuning uchun repozitoriyda yo‘q. Qo‘shish: Windows’dagi `C:\Windows\Fonts` dan **Times New Roman** va **Times New Roman Bold** fayllarini `fonts/times.ttf` va `fonts/timesbd.ttf` nomi bilan nusxalang, serverni qayta ishga tushiring (batafsil: [`fonts/README.md`](fonts/README.md)). Fayllar bo‘lmasa, o‘lchamlari bir xil **Liberation Serif** ishlatiladi.
- Linux’da lokal ishga tushirishda WeasyPrint uchun: `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-liberation` (Docker image’da bular bor). Windows’da: [WeasyPrint o‘rnatish yo‘riqnomasi](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows) (GTK/MSYS2) yoki Docker.
- Namuna va solishtirish: [`docs/pdf/`](docs/pdf/).

## Muhit o‘zgaruvchilari

| O‘zgaruvchi | Ma’nosi | Standart |
|---|---|---|
| `DJANGO_DEBUG` | Ishlab chiqish rejimi | `False` |
| `DJANGO_SECRET_KEY` | Maxfiy kalit (DEBUG=False da majburiy) | — |
| `DJANGO_ALLOWED_HOSTS` | Ruxsat etilgan domenlar, vergul bilan | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | HTTPS manzillar (Railway domeni) | — |
| `DATABASE_URL` | PostgreSQL manzili; bo‘sh bo‘lsa SQLite | SQLite |
| `DJANGO_SECURE_PROXY` | Proksi orqasida HTTPS (Railway’da `True`) | `False` |
| `PORT` | Gunicorn porti (Railway o‘zi beradi) | `8000` |
| `LOGIN_MAX_FAILURES` / `LOGIN_BLOCK_MINUTES` | Login cheklovi | `5` / `15` |

Production’da qo‘shimcha (`.env.prod.example`, [`docs/joylashtirish.md`](docs/joylashtirish.md)):

| O‘zgaruvchi | Ma’nosi | Standart |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings_prod` — xavfsiz sozlamalar (docker-compose.prod.yml o‘zi qo‘yadi) | `config.settings` |
| `DOMAIN` | Caddy uchun domen (`naryad.example.uz`) yoki internetsiz tarmoqda `:80` | — |
| `DJANGO_HTTPS` | HTTPS’ga majburlash, `Secure` cookie, HSTS; ichki tarmoq (HTTP) uchun `False` | `True` |
| `DJANGO_HSTS_SECONDS` | HSTS muddati | 1 yil |
| `DJANGO_LOG_DIR` | Log fayllar papkasi (5 MB × 5) | — (faqat konsol) |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | PostgreSQL | `naryad` / `naryad` / — |
| `BACKUP_TIME` / `BACKUP_KEEP_DAYS` | Kunlik zaxira vaqti va saqlash muddati | `03:00` / `30` |
| `GUNICORN_WORKERS` | Gunicorn jarayonlari | `2` |

## Serverga joylash (production)

```bash
cp .env.prod.example .env        # DOMAIN, maxfiy kalit, parollarni to'ldiring
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
docker compose -f docker-compose.prod.yml exec web python manage.py load_roster
```

- `https://<domen>/health/` → `{"status": "ok"}`. HTTPS sertifikatini Caddy o‘zi oladi.
- Zaxira har kuni 03:00 da `backups/` ga yoziladi (30 kun saqlanadi).
- Tiklash: `sh scripts/restore.sh backups/<fayl>.dump`.
- To‘liq qadam-baqadam yo‘riqnoma (VPS, internetsiz ichki tarmoq, Railway, yangilash, tiklash): [`docs/joylashtirish.md`](docs/joylashtirish.md).
<!-- deploy 1.13.1 -->
