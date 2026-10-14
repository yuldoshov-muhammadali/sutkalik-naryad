# Xavfsizlik bo‘yicha qisqa hisobot (10-bosqich)

Bu hujjat platformada nima himoyalangani, qanday tekshirilgani va qolgan xavflarni qisqacha tushuntiradi.

## 1. Sozlamalar

| Narsa | Qayerda | Holat |
|---|---|---|
| Production sozlamalari alohida | `config/settings_prod.py` (`DJANGO_SETTINGS_MODULE=config.settings_prod`) | ✅ |
| `DEBUG=False` | settings_prod majburan o‘chiradi (muhitda `True` bo‘lsa ham) | ✅ |
| Maxfiy kalit | kamida 50 belgi, aks holda server ishga tushmaydi | ✅ |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | `.env` dan; bo‘sh bo‘lsa server ishga tushmaydi | ✅ |
| HTTPS majburiy | `SECURE_SSL_REDIRECT`, Caddy avtomatik sertifikat (Let’s Encrypt) | ✅ |
| Xavfsiz cookie | `Secure`, `HttpOnly`, `SameSite=Lax`, nomlari `__Secure-` bilan | ✅ |
| HSTS | 1 yil, subdomenlar bilan, preload | ✅ |
| X-Frame-Options | `DENY`; faqat PDF javobi `SAMEORIGIN` (chop etish oynasidagi iframe uchun) | ✅ |
| Content-Security-Policy | `script-src 'self'` — inline JavaScript yo‘q; `frame-ancestors 'none'`, `object-src 'none'`, `form-action 'self'` | ✅ |
| Boshqa sarlavhalar | `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`, `Cross-Origin-Opener-Policy: same-origin` | ✅ |
| Sessiya | 12 soat; parol almashtirilganda boshqa sessiyalar yopiladi | ✅ |

**`python manage.py check --deploy`** (production sozlamalari bilan): `System check identified no issues (0 silenced).`

> B variant (internetsiz ichki tarmoq, HTTPS’siz) uchun `DJANGO_HTTPS=False` qo‘yiladi. Bunda HTTPS’ga yo‘naltirish, `Secure` cookie va HSTS o‘chadi, `check --deploy` bu haqda ogohlantiradi — bu kutilgan holat. Bu variantni faqat tashqi internetdan ajratilgan tarmoqda ishlating.

## 2. Kirish va ruxsatlar

- **Ikki rol:** admin (kurs boshlig‘i) va kursant. Ruxsatlar bitta jadvalda: `naryad/permissions.py` ([`05-rollar.md`](05-rollar.md)). Har bir view `role_required(...)` bilan himoyalangan.
- **Login cheklovi:** bitta login uchun 5 marta noto‘g‘ri parol → 15 daqiqa blok (`LOGIN_MAX_FAILURES`, `LOGIN_BLOCK_MINUTES`). Admin panel kirishi ham shu cheklov ostida.
- **Birinchi kirishda parolni almashtirish majburiy** (`must_change_password`).
- **Parol talablari:** Django’ning 4 ta validatori (uzunlik ≥ 8, oddiy parollar, faqat raqam, login/ismga o‘xshash).
- **Admin panel (`/admin/`)** — faqat admin roli va superuser.
- **Kursant boshqa kursantni ko‘ra olmaydi** — URL’ni qo‘lda yozsa ham. Kursant kartochkasi (`/kursantlar/<id>/`) faqat o‘ziniki bo‘lsa ochiladi (aks holda 403). Qoralama sutka, uning PDF’i va chop etish sahifasi kursantga 404. Statistika sahifasi va Excel eksport — faqat admin.

### Ruxsatlar auditi (avtomatik test)

`tests/test_security.py` loyihadagi **har bir URL** ni uch holatda tekshiradi:

| Kim | Natija |
|---|---|
| Kirmagan foydalanuvchi | hamma sahifa → kirish sahifasiga yo‘naltiriladi (faqat `/kirish/` ochiq) |
| Kursant | faqat: bosh sahifa, parol, o‘z kartochkasi, tasdiqlangan sutkalar, ularning PDF’i va chop etish sahifasi; qolgani 403 / 404 |
| Kursant, POST so‘rovlari | tuzish, almashtirish, tasdiqlash, bekor qilish, o‘chirish, kursant va sababli holat o‘zgartirish — hammasi 403, bazada hech narsa o‘zgarmaydi |
| Admin | hamma sahifa ochiladi |

Yangi URL qo‘shilsa, test uni ro‘yxatda talab qiladi (`test_every_url_is_covered_by_audit`) — ruxsati tekshirilmagan sahifa qolib ketmaydi.

## 3. Ma’lumotlar va yuklanadigan fayllar

- **CSRF** — barcha POST shakllar va HTMX so‘rovlarida.
- **SQL injection** — faqat Django ORM, xom SQL yo‘q (`/health/` dagi `SELECT 1` dan tashqari).
- **XSS** — shablonlar avtomatik ekranlaydi; `|safe` faqat dasturchi yozgan matnlarda (forma izohlari, PDF shrift CSS’i), foydalanuvchi kiritgan ma’lumotda emas; CSP qo‘shimcha himoya.
- **Excel import (kursantlar):**
  - faqat `.xlsx`, hajmi ≤ 2 MB (so‘rov 3 MB dan oshsa Django o‘zi rad etadi);
  - fayl haqiqiy Excel (ZIP + `xl/` ichki tuzilma) ekani tekshiriladi;
  - ochilgandagi hajmi ≤ 30 MB (“zip bomba”dan himoya);
  - ko‘pi bilan 1000 qator va 30 ustun o‘qiladi;
  - bitta xato bo‘lsa hech narsa yozilmaydi (avval ko‘rib chiqish, keyin tasdiqlash).
- **O‘tgan tarix importi** (`import_history`) — faqat server buyrug‘i, veb orqali yuklanmaydi.
- **Bir vaqtda tahrirlash** — sutka versiyasi (`version`) va qator qulfi: eskirgan sahifadan o‘zgartirish rad etiladi.
- **Jurnal** — har bir tuzish, almashtirish, tasdiqlash, bekor qilish, o‘chirish kim va qachon qilgani bilan yoziladi; sabab majburiy.

## 4. Server va zaxira

- Web konteyner `root` emas, `app` (uid 1000) foydalanuvchisi bilan ishlaydi.
- PostgreSQL porti tashqariga ochilmaydi (faqat ichki Docker tarmog‘i); tashqariga faqat Caddy (80/443).
- `/health/` — faqat “ok” yoki “xato” qaytaradi, ichki ma’lumot bermaydi.
- Loglar konsolga va faylga yoziladi (5 MB × 5 fayl), Docker loglari ham cheklangan (10 MB × 5).
- Har kuni zaxira (`pg_dump`), 30 kun saqlanadi; tiklash sinab ko‘rilgan ([`joylashtirish.md`](joylashtirish.md)).

## 5. Qolgan xavflar va tavsiyalar

1. **Zaxira nusxalar o‘sha serverda turadi.** Server diski buzilsa, zaxira ham yo‘qoladi — haftada bir marta `backups/` ni boshqa joyga (fleshka, boshqa kompyuter) ko‘chiring.
2. **Ikki bosqichli autentifikatsiya yo‘q.** Admin paroli kuchli bo‘lishi va hech kimga berilmasligi kerak.
3. **Vaqtinchalik parollar Excel faylda chiqariladi** (`create_cadet_accounts`) — chop etilgach fayl o‘chirilishi kerak.
4. **Login cheklovi login bo‘yicha:** kimdir boshqa kursantning loginini ataylab 5 marta xato kiritsa, o‘sha kursant 15 daqiqa kira olmaydi (boshqalarga ta’sir qilmaydi). Admin kerak bo‘lsa blokni admin panel → *Login cheklovlari* dan o‘chiradi.
5. **B variant (HTTP)** — parollar tarmoqda shifrlanmagan holda yuradi; faqat ishonchli ichki tarmoqda ishlating.
