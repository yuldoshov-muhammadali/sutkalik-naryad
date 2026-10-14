# Foydalanuvchi qo‘llanmasi

Sutkalik naryad platformasi 2-kurs sutkalik naryad ro‘yxatini tarix asosida, adolatli va avtomatik tuzadi.
- Ro‘yxatni **dastur** tuzadi. Kurs boshlig‘i uni tekshiradi, kerak bo‘lsa sabab ko‘rsatib tuzatadi va tasdiqlaydi.
- Kursantlar faqat tasdiqlangan ro‘yxatlarni va o‘z naryadlarini ko‘radi.

Bir sahifalik qisqa yo‘riqnoma (chop etib osib qo‘yish uchun): [`qollanma/qisqa-yoriqnoma.pdf`](qollanma/qisqa-yoriqnoma.pdf).

**Muhim tushunchalar**
- **Sutka** — shu sana 18:00 dan ertasi kuni 18:00 gacha. “13-oktabr sutkasi” = 13-oktabr 18:00 → 14-oktabr 18:00.
- **2-kurs haftasi** — yakshanba 18:00 dan keyingi yakshanba 18:00 gacha (7 sutka). Kurslar haftama-hafta almashadi, shuning uchun 2-kurs haftasini kurs boshlig‘i o‘zi ochadi.
- **Qoralama** — dastur tuzgan, hali tasdiqlanmagan ro‘yxat. Uni faqat admin ko‘radi.
- **Tasdiqlangan** — rasmiy ro‘yxat. Uni hamma ko‘radi va PDF qilib chop etadi.

---

## 1. Kurs boshlig‘i (admin) uchun

### 1.1. Kirish
Brauzerda platforma manzilini oching (masalan `https://naryad.example.uz`), login va parolni kiriting.
- 5 marta noto‘g‘ri parol kiritilsa, login 15 daqiqaga bloklanadi.
- Birinchi kirishda parolni almashtirish so‘ralishi mumkin.

<img src="qollanma/rasmlar/01-kirish-telefon.png" alt="Kirish sahifasi" width="300">

### 1.2. Bosh sahifa
Bosh sahifada:
- joriy 2-kurs haftasi va uning 7 sutkasi holati;
- **“Keyingi qadam”** tugmasi — hozir nima qilish kerakligini aytadi;
- har guruhning **adolat belgisi**.

![Bosh sahifa](qollanma/rasmlar/13-bosh-sahifa-tasdiqdan-keyin.png)

### 1.3. Haftani ochish
**Haftalar** → yakshanba sanasini tanlang. Pastda shu haftaning 7 sutkasi ko‘rinadi → **Haftani ochish**.
Faqat yakshanba tanlanadi; haftalar bir-biriga to‘g‘ri kelmasligi tekshiriladi.

![Hafta ochish](qollanma/rasmlar/03-hafta-ochish.png)

### 1.4. Sutkani tuzish
Haftalardan sutkani bosing → **Tuzish**.
- Dastur ro‘yxatni tarix asosida tuzadi:
  - guruhlar joylar bo‘yicha aylanadi (Markaz → 1-NO‘J → 2-NO‘J → 1-Yotoqxona → O‘quv binosi → Patrul);
  - guruh ichida eng kam navbatda turganlar tanlanadi.
- Sutkalar ketma-ket tuziladi: avvalgisi tasdiqlanmasa, keyingisini tuzib bo‘lmaydi.
- Kecha navbatda turgan yoki sababli yo‘q (kasal, ta’til) kursant hech qachon qo‘yilmaydi. O‘rin yetmasa, bo‘sh qoladi va qizil ogohlantirish chiqadi.

![Qoralama](qollanma/rasmlar/05-qoralama.png)

### 1.5. Almashtirish (qo‘lda tuzatish)
Kerakli qatordagi **Almashtirish** tugmasini bosing.
- Oynada nomzodlar algoritm tartibida chiqadi: eng munosibi birinchi, yonida uning hisob-kitobi.
- Taqiqlangan nomzodlar (kecha navbatda bo‘lgan, sababli yo‘q, bugun boshqa joyda turgan) tanlab bo‘lmaydi.
- **Sabab majburiy:** kasal / ta’til / sababli / boshqa.
  - “Kasal” yoki “Ta’til” tanlansa, olib tashlangan kursantga shu sutka uchun sababli holat avtomatik yoziladi.
- Har bir o‘zgarish **jurnalga** yoziladi: kim, qachon, nima, nega.

| Almashtirish oynasi | Natija |
|---|---|
| ![Almashtirish oynasi](qollanma/rasmlar/06-almashtirish-oynasi.png) | ![Almashtirildi](qollanma/rasmlar/07-almashtirilgan.png) |

Qo‘lda qo‘yilgan kursant yonida ✎ belgisi turadi.

Bitta joy ichida ikki kursantning lavozimini almashtirish uchun **Lavozimlarni almashtirish** tugmasi bor.

Boshqa amallar:
- **Qayta tuzish** — qo‘lda kiritilgan o‘zgarishlar o‘chadi, oldin so‘raladi.
- **Qoralamani o‘chirish** — faqat eng oxirgi qoralama, sabab bilan.

### 1.6. Tasdiqlash
Ogohlantirishlar qolmagach (bo‘sh o‘rin, faol emas yoki sababli yo‘q kursant), **Tasdiqlash** tugmasi faol bo‘ladi.
- Tasdiqlangan ro‘yxatni o‘zgartirib bo‘lmaydi.
- Kerak bo‘lsa, **Tasdiqni bekor qilish…** (sabab majburiy) bilan qayta qoralamaga qaytariladi. Keyingi sutka allaqachon tuzilgan bo‘lsa, avval o‘shani bekor qilish kerak.

![Tasdiqlangan](qollanma/rasmlar/08-tasdiqlangan.png)

### 1.7. PDF va chop etish
- **PDF yuklab olish** — rasmiy shakldagi A4 ro‘yxat (`naryad_2026-10-13.pdf`).
- **Chop etish** — PDF ochiladi va chop etish oynasi avtomatik chiqadi. Telefonda **“PDF’ni alohida ochish”** havolasidan foydalaning.
- **Hafta PDF** (Haftalar sahifasida) — 7 sutka, har biri alohida sahifada.
- Qoralama PDF’ida “QORALAMA” yozuvi bo‘ladi.

### 1.8. Jurnal
Sutka sahifasidagi **Jurnal** tugmasi shu sutkadagi barcha amallarni vaqt tartibida ko‘rsatadi: tuzish, almashtirish, tasdiqlash, bekor qilish.

![Jurnal](qollanma/rasmlar/09-jurnal.png)

### 1.9. Sababli holatlar (kasal, ta’til)
**Sababli holatlar** sahifasida kursant, sabab va sanalar (dan–gacha) kiritiladi. Shu kunlarda dastur uni naryadga qo‘ymaydi.
- Tugash sanasini o‘zgartirish mumkin (masalan, erta tuzalsa).
- Hali boshlanmagan yozuvni o‘chirish mumkin.

![Sababli holatlar](qollanma/rasmlar/10-sababli-holatlar.png)

### 1.10. Kursantlarni boshqarish
**Kursantlar** sahifasida:
- guruhlar bo‘yicha sonlar, familiya bo‘yicha qidiruv, filtrlar;
- **Kursant qo‘shish**, tahrirlash. Qisqa ism (`Familiya I`) avtomatik yasaladi;
- **Faolsizlantirish** (sabab bilan): kursant o‘chirilmaydi, tarixi qoladi, lekin naryadga tushmaydi va tizimga kira olmaydi;
- **Excel import:** avval ko‘rib chiqish, keyin tasdiqlash. Shablon sahifada; fayl ≤ 2 MB, faqat `.xlsx`.

- **Naryaddan ozod qilish** (komandirlar, kurs starshinasi, pisar, kaptyorchik): kursant kartochkasida **Naryaddan ozod qilish…** — lavozim va sabab majburiy.
  - Kursant faol qoladi va tizimga kiradi, faqat sutkalik naryadga qo‘yilmaydi.
  - Ro‘yxatda “ozod” belgisi bor, filtr: *Naryaddan ozod* / *Naryadga chiqadi*.
  - Lavozimdan bo‘shasa — **Naryadga qaytarish…**. Algoritm uni hisob bo‘yicha o‘zi oldinga qo‘yadi.
- Guruhlar jadvalidagi **“Naryadga chiqadi”** ustuni — ozodlarsiz o‘g‘il bolalar soni (jami 78).

Kursant kartochkasida: naryadlar tarixi, joylar va lavozimlar bo‘yicha sonlar, guruh o‘rtachasi bilan solishtirish, o‘zgarishlar jurnali.

![Kursantlar](qollanma/rasmlar/11-kursantlar.png)

### 1.11. Statistika va ogohlantirishlar
**Statistika** sahifasi hisobni faqat tasdiqlangan sutkalar bo‘yicha qiladi.

**Davr:** butun tarix, sanadan sanagacha yoki bitta 2-kurs haftasi.

**Kursant × joy jadvali** (guruh tanlanadi):
- rang qanchalik to‘q bo‘lsa, shuncha ko‘p;
- telefonda jadval yonga suriladi, ism ustuni qotib turadi.

**Adolat belgisi** — har guruh ichida jami naryadlar farqi:

| Belgi | Farq | Ma’nosi |
|---|---|---|
| 🟢 yashil | ≤ 1 | adolatli |
| 🟡 sariq | 2 | diqqat |
| 🔴 qizil | ≥ 3 | adolatsiz — sababini tekshiring |

**Boshqa bo‘limlar:**
- **Ketma-ket bir joy** — kimning ketma-ket ikki naryadi bir joyga tushgani.
- **Qizlar uchun** — ketma-ket ikki marta navbatchi bo‘lganlar.
- **Guruhlar kesimi** — har guruh har joyni necha marta bergani. Kichik guruhda bir kursantga ko‘proq naryad to‘g‘ri keladi — bu qabul qilingan qoida.
- **Qo‘lda tuzatishlar nazorati:**
  - almashtirishlar sabab va kim tomonidan qilingani bo‘yicha;
  - har kursant necha marta qo‘lda qo‘yilgan va olib tashlangan;
  - **qizil ro‘yxat** — guruh o‘rtachasidan sezilarli ko‘p (≥ 2 marta va ≥ 2 baravar) qo‘lda qo‘yilganlar. Bu qog‘ozdagi adolatsizlik qaytmasligi uchun.
- **Excel’ga yuklab olish** — barcha jadvallar bitta faylda, har biri alohida varaqda.

![Statistika](qollanma/rasmlar/12-statistika.png)

### 1.12. Telefonda
Hamma sahifa telefonga moslangan: menyu o‘ng yuqoridagi **Menyu** tugmasida.

| Sutka (telefon) | Menyu |
|---|---|
| <img src="qollanma/rasmlar/14-sutka-telefon.png" width="260"> | <img src="qollanma/rasmlar/15-menyu-telefon.png" width="260"> |

### 1.13. Boshqaruv paneli
**Boshqaruv paneli** (`/admin/`) — kamdan-kam kerak bo‘ladigan sozlamalar uchun:
- imzo (unvon, F.I.Sh.), “Tasdiqlayman” bloki;
- boshlang‘ich guruh → joy taqsimoti;
- foydalanuvchilar va login cheklovlari.

Unga faqat admin kiradi.

---

## 2. Kursant uchun

### 2.1. Kirish va parol
- **Login:** `familiya.ism`, masalan `aliyev.vali`.
- Vaqtinchalik parolni kurs boshlig‘i beradi.
- Birinchi kirishda parolni almashtirish shart. Yangi parol kamida 8 belgi bo‘lsin, faqat raqamlardan iborat yoki oddiy (`12345678`, `parol123`) bo‘lmasin.
- Keyin parolni **Menyu → Parol** orqali istalgan vaqtda almashtirish mumkin.

<img src="qollanma/rasmlar/20-parol-almashtirish.png" alt="Parolni almashtirish" width="300">

### 2.2. Mening naryadlarim
Bosh sahifada:
- **keyingi naryadingiz** (tasdiqlangan bo‘lsa);
- shu haftadagi va jami naryadlar soni;
- oxirgi naryadlar.

**Mening tarixim** — barcha naryadlaringiz, joylar va lavozimlar bo‘yicha sonlar, hamda guruh o‘rtachasi bilan solishtirish. Boshqa kursantlarning ismlari ko‘rinmaydi.

| Bosh sahifa | Mening tarixim |
|---|---|
| <img src="qollanma/rasmlar/16-kursant-bosh-sahifa.png" width="260"> | <img src="qollanma/rasmlar/17-kursant-mening-tarixim.png" width="260"> |

### 2.3. Tasdiqlangan ro‘yxatlar
**Tasdiqlangan naryadlar** — barcha tasdiqlangan sutkalar.
- Sutkani bossangiz, to‘liq ro‘yxat ochiladi. Uni **PDF** qilib yuklab olish yoki chop etish mumkin.
- Qoralamalar kursantga ko‘rinmaydi.

| Ro‘yxat | Sutka |
|---|---|
| <img src="qollanma/rasmlar/18-kursant-tasdiqlangan-naryadlar.png" width="260"> | <img src="qollanma/rasmlar/19-kursant-sutka.png" width="260"> |

Kursantga ruxsat berilmagan sahifa ochilsa, “Ruxsat yo‘q” xabari chiqadi. Masalan, statistika yoki boshqa kursantning kartochkasi.

---

## 3. Tez-tez beriladigan savollar

**Nega meni (yoki uni) qo‘ydi?**
Dastur guruh ichida avval shu haftada kam turganlarni tanlaydi. Keyin quyidagilarga qaraydi:
1. jami naryadlar kam bo‘lgan;
2. o‘tgan safar boshqa joyda turgan;
3. shu joyda kam turgan;
4. uzoqroq dam olgan.

Batafsil: [`02-algoritm.md`](02-algoritm.md).

**Kasal bo‘lib qoldim.** Kurs boshlig‘iga ayting: u sababli holat kiritadi va qoralamada sizni almashtiradi.

**Parolimni unutdim.** Kurs boshlig‘i boshqaruv panelida yangi vaqtinchalik parol beradi.

**Nega guruhimizga ko‘proq naryad tushadi?** Joylar guruhlar o‘rtasida teng aylanadi. Kichik guruhda kursant kam bo‘lgani uchun har biriga ko‘proq to‘g‘ri keladi. Adolat guruh **ichida** o‘lchanadi.
