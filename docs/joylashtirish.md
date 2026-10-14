# Serverga joylashtirish yo‘riqnomasi

Bu yo‘riqnoma serverlar bilan ishlamagan odam uchun yozilgan: har bir buyruqni ko‘chirib, ketma-ket bajaring.
Uch xil variant bor — o‘zingizga mosini tanlang:

| Variant | Qachon | Manzil |
|---|---|---|
| **A. VPS + domen** (tavsiya) | Internetdan, telefondan ham kirish kerak | `https://naryad.sizning-domen.uz` |
| **B. Ichki kompyuter** | Internet yo‘q, faqat institut ichki tarmog‘i | `http://192.168.1.10` |
| **C. Railway** | Server boshqarishni xohlamasangiz (pullik bulut) | `https://<loyiha>.up.railway.app` |

Har uch variantda bir xil dastur ishlaydi:
- **web** — Django va gunicorn;
- **db** — PostgreSQL 16;
- **caddy** — HTTPS, sertifikat avtomatik;
- **backup** — har kuni zaxira nusxa.

---

## A variant: oddiy VPS (Ubuntu) + domen

### 1. Nima kerak
- VPS server: Ubuntu 22.04 yoki 24.04, kamida 1 GB RAM (2 GB tavsiya), 20 GB disk. Har qanday provayder bo‘ladi.
- Domen yoki subdomen, masalan `naryad.example.uz`.
- Kompyuteringizda terminal: Windows’da **PowerShell**, macOS/Linux’da **Terminal**.

### 2. Domenni serverga yo‘naltirish
Domen provayderingiz panelida **A yozuv** qo‘shing:

| Turi | Nomi | Qiymati |
|---|---|---|
| A | `naryad` | serveringiz IP manzili, masalan `203.0.113.25` |

15–60 daqiqa kuting. Tekshirish: `ping naryad.example.uz` serveringiz IP’sini ko‘rsatishi kerak.

### 3. Serverga ulanish va tayyorlash
```bash
ssh root@203.0.113.25            # provayder bergan parol yoki kalit bilan
apt update && apt upgrade -y
apt install -y git ufw
ufw allow OpenSSH && ufw allow 80 && ufw allow 443 && ufw --force enable
timedatectl set-timezone Asia/Tashkent
```

### 4. Docker o‘rnatish
```bash
curl -fsSL https://get.docker.com | sh
docker --version && docker compose version     # ikkalasi ham versiya chiqarishi kerak
```

### 5. Dasturni serverga ko‘chirish
GitHub’dan:
```bash
cd /opt && git clone https://github.com/yuldoshov-muhammadali/sutkalik-naryad.git
cd /opt/sutkalik-naryad
```
Yoki zip fayldan. Kompyuteringizda bajaring:
```bash
scp sutkalik-naryad.zip root@203.0.113.25:/opt/
```
So‘ng serverda:
```bash
cd /opt && apt install -y unzip && unzip sutkalik-naryad.zip && cd sutkalik-naryad
```

### 6. `.env` faylini to‘ldirish
```bash
cp .env.prod.example .env
python3 -c "import secrets; print(secrets.token_urlsafe(50))"   # → DJANGO_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(24))"   # → POSTGRES_PASSWORD
nano .env
```
`.env` ichida o‘zgartiring:
```ini
DOMAIN=naryad.example.uz
DJANGO_SECRET_KEY=<birinchi chiqqan uzun qator>
DJANGO_ALLOWED_HOSTS=naryad.example.uz
DJANGO_CSRF_TRUSTED_ORIGINS=https://naryad.example.uz
DJANGO_HTTPS=True
POSTGRES_PASSWORD=<ikkinchi chiqqan qator>
```
Saqlash: `Ctrl+O`, `Enter`, `Ctrl+X`. **`.env` faylini hech kimga bermang va GitHub’ga yuklamang.**

### 7. (Ixtiyoriy) Times New Roman shrifti
Windows kompyuterdagi `C:\Windows\Fonts\times.ttf` va `timesbd.ttf` fayllarini serverdagi `fonts/` papkasiga nusxalang:
```bash
scp times.ttf timesbd.ttf root@203.0.113.25:/opt/sutkalik-naryad/fonts/
```
Bo‘lmasa, o‘lchamlari bir xil bo‘lgan Liberation Serif ishlatiladi.

### 8. Ishga tushirish
```bash
docker compose -f docker-compose.prod.yml up -d --build
```
Birinchi marta 3–5 daqiqa davom etadi. Tekshirish:
```bash
docker compose -f docker-compose.prod.yml ps
```
To‘rttala servis `Up … (healthy)` holatida bo‘lishi kerak: `web`, `db`, `caddy`, `backup`.

Brauzerda `https://naryad.example.uz/health/` sahifasi `{"status": "ok", "database": "ok"}` ko‘rsatsa, hammasi joyida.

### 9. Birinchi admin (kurs boshlig‘i)
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```
Login va parol (kamida 8 belgi) so‘raladi, email bo‘sh qoldirsa bo‘ladi. Shu login bilan `https://naryad.example.uz/kirish/` orqali kiring.

### 10. Kursantlar ro‘yxati va tarix
Kursantlar ro‘yxati — **faqat birinchi marta**:
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py load_roster
```

Keyin **bittasini** tanlang.

**a) Qog‘ozdagi o‘tgan sutkalar bor bo‘lsa.** `data/tarix_shablon.xlsx` ni to‘ldiring (namuna: `data/tarix_namuna.xlsx`). So‘ng:
```bash
docker compose -f docker-compose.prod.yml cp tarix.xlsx web:/tmp/tarix.xlsx
docker compose -f docker-compose.prod.yml exec web python manage.py import_history /tmp/tarix.xlsx --dry-run
docker compose -f docker-compose.prod.yml exec web python manage.py import_history /tmp/tarix.xlsx
```
`--dry-run` faqat tekshiradi, bazaga yozmaydi; xato bo‘lsa qator raqami bilan chiqadi.

**b) Tarix bo‘lmasa.** Saytda: **Boshqaruv paneli → Sozlamalar → Boshlang‘ich guruh → joy taqsimoti**. 6 ta joyning har biriga bitta guruh tanlang.

### 11. Kursantlarga akkaunt berish
```bash
docker compose -f docker-compose.prod.yml exec web python manage.py create_cadet_accounts --output-dir /tmp
docker compose -f docker-compose.prod.yml exec web sh -c 'ls /tmp/akkauntlar_*.xlsx'
docker compose -f docker-compose.prod.yml cp web:/tmp/akkauntlar_2026-10-13.xlsx .
```
Uchinchi buyruqdagi fayl nomini ikkinchisida chiqqan nom bilan almashtiring. Faylni kompyuteringizga oling, chop eting va **o‘chiring**:
```bash
scp root@203.0.113.25:/opt/sutkalik-naryad/akkauntlar_*.xlsx .
```
Kursant birinchi kirishda parolini almashtiradi.

Tayyor! Foydalanish: [`qollanma.md`](qollanma.md).

---

## B variant: internetsiz ichki tarmoq (institut kompyuteri)

Server — institutdagi doim yoqiq turadigan bitta kompyuter. Unda Ubuntu yoki Windows 10/11 + Docker Desktop bo‘lishi mumkin. Kursantlar shu tarmoqdagi telefon yoki kompyuterdan `http://<kompyuter IP>` orqali kiradi.
- HTTPS bo‘lmaydi.
- Shuning uchun faqat tashqi internetdan ajratilgan, ishonchli ichki tarmoqda ishlating (qarang: [`xavfsizlik.md`](xavfsizlik.md)).

### 1. Internet bor kompyuterda tayyorlab olish (bir marta)
Docker o‘rnatilgan, internetli istalgan kompyuterda, loyiha papkasida bajaring:
```bash
docker compose -f docker-compose.prod.yml build web
docker pull postgres:16-alpine
docker pull caddy:2-alpine
docker save -o naryad-images.tar sutkalik-naryad:latest postgres:16-alpine caddy:2-alpine
```
Fleshkaga ko‘chiring:
- `naryad-images.tar` (~400 MB);
- butun loyiha papkasi;
- Windows bo‘lsa, Docker Desktop o‘rnatuvchisi;
- Ubuntu bo‘lsa, Docker `.deb` paketlari: [docs.docker.com/engine/install/ubuntu](https://docs.docker.com/engine/install/ubuntu/#install-from-a-package).

### 2. Ichki kompyuterda o‘rnatish
1. **Docker’ni o‘rnating:**
   - Windows — Docker Desktop o‘rnatuvchisini ishga tushiring;
   - Ubuntu — `sudo dpkg -i *.deb`.
2. **Image’larni yuklang:**
   ```bash
   docker load -i naryad-images.tar
   ```
3. **Kompyuterga doimiy IP bering** (masalan `192.168.1.10`). Buni tarmoq administratori qiladi yoki routerda “DHCP reservation” orqali sozlanadi.
4. **`.env` faylini to‘ldiring.** `.env.prod.example` dan nusxa oling (A variant, 6-qadam) va quyidagilarni yozing:
   ```ini
   DOMAIN=:80
   DJANGO_HTTPS=False
   DJANGO_ALLOWED_HOSTS=192.168.1.10,localhost
   DJANGO_CSRF_TRUSTED_ORIGINS=http://192.168.1.10
   DJANGO_SECRET_KEY=<uzun tasodifiy qator>
   POSTGRES_PASSWORD=<uzun tasodifiy qator>
   ```
   Tasodifiy qator yaratish (Windows PowerShell’da ham ishlaydi):
   ```bash
   docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
   Agar `python:3.12-slim` yuklanmagan bo‘lsa, istalgan 50+ belgili tasodifiy qator yozing.
5. **Ishga tushiring.** `--build` **yozmang**, image’lar fleshkadan yuklangan:
   ```bash
   docker compose -f docker-compose.prod.yml up -d
   ```
6. **Brandmauer:** 80-portni oching. Windows’da “Windows Defender Firewall → Inbound rules → Port 80”. Ubuntu’da `sudo ufw allow 80`.
7. **Tekshirish:** boshqa kompyuterdan `http://192.168.1.10/health/` ochilsin.
8. **Admin, kursantlar ro‘yxati, tarix va akkauntlar** — A variantning 9–11-qadamlari bilan bir xil.

Windows’da kompyuter qayta yoqilganda dastur avtomatik ishga tushishi uchun: Docker Desktop → *Settings → General → Start Docker Desktop when you sign in*. Servislar `restart: unless-stopped` bilan o‘zi ko‘tariladi.

---

## C variant: Railway (qisqacha)

1. [railway.app](https://railway.app) da yangi loyiha yarating:
   - **Deploy from GitHub repo** — repozitoriyni tanlang;
   - **+ New → Database → PostgreSQL** qo‘shing.
2. Web servis **Variables** bo‘limiga yozing:
   - `DJANGO_SETTINGS_MODULE=config.settings_prod`
   - `DJANGO_SECRET_KEY=<uzun tasodifiy qator>`
   - `DATABASE_URL=${{Postgres.DATABASE_URL}}`
   - `DJANGO_ALLOWED_HOSTS=<loyiha>.up.railway.app`
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://<loyiha>.up.railway.app`
   - `DJANGO_HTTPS=True`
3. Web servis **Settings** bo‘limida:
   - *Healthcheck Path* — `/health/`;
   - *Networking* — **Generate Domain**.
4. Buyruqlarni Railway CLI orqali bajaring:
   ```bash
   railway run python manage.py createsuperuser
   railway run python manage.py load_roster
   ```
5. Zaxira: `backup` servisi faqat A/B variantlarda ishlaydi. Railway’da PostgreSQL servisining zaxira (*Backups*) imkoniyatini yoqing yoki vaqti-vaqti bilan `railway run pg_dump` qiling.

---

## Yangilash (yangi versiya chiqqanda)

1. **Avval zaxira oling:**
   ```bash
   cd /opt/sutkalik-naryad
   docker compose -f docker-compose.prod.yml exec backup sh /scripts/backup.sh
   ```
2. **Yangi kodni oling:**
   - git bilan: `git pull`;
   - zip bilan: yangi zipni ochib, eski papka ustidan nusxalang. `.env`, `backups/` va `fonts/*.ttf` saqlanib qolsin.
3. **Qayta yig‘ib ishga tushiring.** Migratsiyalar avtomatik bajariladi:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   docker compose -f docker-compose.prod.yml ps        # hammasi (healthy)
   ```
4. **Saytga kirib tekshiring.** Muammo bo‘lsa, quyidagi “Zaxiradan tiklash” bo‘limiga qarang.

B variantda yangi image internetli kompyuterda yig‘iladi va `docker save` / `docker load` bilan ko‘chiriladi (1-qadamdagidek).

---

## Zaxira nusxa

- **Avtomatik:** `backup` servisi har kuni soat **03:00** da (`BACKUP_TIME`) bazaning to‘liq nusxasini `backups/naryad_YYYY-MM-DD_HHMMSS.dump` fayliga yozadi.
- **Saqlash muddati:** oxirgi **30 kun** saqlanadi (`BACKUP_KEEP_DAYS`), eskilari o‘zi o‘chadi.
- **Qo‘lda, hozir:**
  ```bash
  docker compose -f docker-compose.prod.yml exec backup sh /scripts/backup.sh
  ```
- **Ro‘yxat:** `ls -lh backups/`
- **Muhim — server buzilsa, zaxira ham yo‘qolmasin.** Haftada bir marta zaxirani boshqa joyga (kompyuteringiz, fleshka) ko‘chiring:
  ```bash
  scp root@203.0.113.25:/opt/sutkalik-naryad/backups/naryad_*.dump .
  ```

## Zaxiradan tiklash (qadam-baqadam)

> Bu qadamlar 10-bosqichda production Docker’da sinab ko‘rilgan. Sinov tartibi:
> 1. Zaxira olindi (82 faol kursant).
> 2. Bazada ma’lumot o‘zgartirildi (100 faol).
> 3. `restore.sh` ishga tushirildi.
> 4. Baza aynan zaxiradagi holatga qaytdi (82 faol).

1. Qaysi zaxiraga qaytishni tanlang:
   ```bash
   cd /opt/sutkalik-naryad
   ls -lt backups/ | head
   ```
2. Tiklang:
   ```bash
   sh scripts/restore.sh backups/naryad_2026-10-13_030000.dump
   ```
   Skript “Davom etasizmi?” deb so‘raydi — `ha` deb yozing. So‘ng o‘zi:
   1. web’ni to‘xtatadi;
   2. **hozirgi** bazadan ham xavfsizlik uchun zaxira oladi (xato fayl tanlansa, orqaga qaytish mumkin);
   3. bazani tanlangan zaxira holatiga qaytaradi;
   4. web’ni ishga tushiradi (migratsiyalar avtomatik) va `/health/` ni tekshiradi.
3. `Tayyor: baza … holatiga qaytarildi.` yozuvi chiqsa, saytga kirib tekshiring.

**Windows’da (B variant)** `sh` buyrug‘i bo‘lmasa, PowerShell’da qo‘lda bajaring. Bular har qanday tizimda ishlaydi:
```powershell
docker compose -f docker-compose.prod.yml stop web
docker compose -f docker-compose.prod.yml exec backup sh /scripts/backup.sh
docker compose -f docker-compose.prod.yml cp backups/naryad_2026-10-13_030000.dump db:/tmp/tiklash.dump
docker compose -f docker-compose.prod.yml exec db pg_restore --clean --if-exists --no-owner --no-privileges -U naryad -d naryad /tmp/tiklash.dump
docker compose -f docker-compose.prod.yml start web
```
`-U naryad -d naryad` — `.env` dagi `POSTGRES_USER` va `POSTGRES_DB` qiymatlari (standart: `naryad`).

**Butunlay yangi serverga ko‘chirish:**
1. Yangi serverda A variantning 1–8-qadamlarini bajaring. `createsuperuser` va `load_roster` ni bajarmang.
2. Zaxira faylini `backups/` ga nusxalang.
3. `sh scripts/restore.sh backups/<fayl>.dump` ni ishga tushiring.

---

## Muammolar va yechimlar

| Belgisi | Sabab | Yechim |
|---|---|---|
| `https://` ochilmaydi, sertifikat xatosi | Domen hali serverga yo‘nalmagan yoki 80/443 port yopiq | `ping domen` → IP to‘g‘rimi; `ufw status`; `docker compose -f docker-compose.prod.yml logs caddy` |
| “Bad Request (400)” | Domen `DJANGO_ALLOWED_HOSTS` da yo‘q | `.env` ni tuzating, so‘ng `docker compose -f docker-compose.prod.yml up -d` |
| Kirishda “CSRF xatosi” (403) | `DJANGO_CSRF_TRUSTED_ORIGINS` noto‘g‘ri | `https://domen` (B variantda `http://IP`) yozing |
| B variantda doim `https` ga o‘tib ketadi | `DJANGO_HTTPS=False` yozilmagan | `.env` ni tuzating va qayta ishga tushiring |
| `web` servisi `unhealthy` | Baza ulanmagan yoki xato | `docker compose -f docker-compose.prod.yml logs web --tail 50` |
| Admin parolini unutdim | — | `docker compose -f docker-compose.prod.yml exec web python manage.py changepassword <login>` |
| Kursant “login bloklandi” deydi | 5 marta xato parol | 15 daqiqa kuting yoki Boshqaruv paneli → *Login cheklovlari* → yozuvni o‘chiring |
| Disk to‘lib qoldi | Eski zaxira/loglar | `BACKUP_KEEP_DAYS` ni kamaytiring; `docker system prune` |

Loglar:
- `docker compose -f docker-compose.prod.yml logs -f web` — jonli;
- Django log fayli konteyner ichida `/app/logs/naryad.log` (5 MB × 5 fayl).

Docker loglari har servis uchun 10 MB × 5 fayl bilan cheklangan.
