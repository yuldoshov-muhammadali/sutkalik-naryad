# 2-bosqich: taqsimlash algoritmi

> Manbalar: `CLAUDE.md` (4- va 10-bo‘limlar), `docs/01-talablar-va-sxema.md`.
> Kod: `naryad/engine/` — faqat Python standart kutubxonasi, Django’ga bog‘liq emas.

## 1. Modul tuzilishi

| Fayl | Vazifasi |
|---|---|
| `naryad/engine/models.py` | Dataclass’lar: `Post`, `Slot` (lavozim), `Cadet`, `Record` (tarix yozuvi), `Absence`, `CandidateScore`, `PickResult`, `Assignment`, `DayResult` |
| `naryad/engine/config.py` | 7 joy, 20 o‘rin, lavozimlar, PDF yozuvlari va aylanish zanjiri; import paytida 17 + 3 = 20 ekanini o‘zi tekshiradi |
| `naryad/engine/allocator.py` | `week_bounds`, `rotate_groups`, `pick_cadets`, `assign_roles`, `generate_day` |
| `naryad/engine/names.py` | Apostroflarni birxillashtirish (`o‘`, `g‘`, `’`) va PDF qisqa shakli (`Sa’dullayev B`, `Shavkatov Sh`, `G‘ayratov G‘`) |
| `scripts/build_roster.py` | `data/2-KURS ROYXATI.doc` → `data/roster.json` (100 kishi, sonlarni CLAUDE.md 2-bo‘lim bilan tekshiradi) |
| `scripts/demo.py` | Haqiqiy ro‘yxat bilan namunaviy hisob (quyidagi 5–7-bo‘limlar shu skript natijasi) |
| `tests/` | pytest testlari (32 ta) |

## 2. Psevdokod

```
generate_day(sana, kursantlar, tarix, yo‘qliklar, boshlang‘ich_taqsimot):
    tarix ← tarixdagi sana’dan OLDINGI yozuvlar (faqat tasdiqlangan sutkalar)

    # 1-daraja: guruh → joy
    agar tarixda o‘g‘il bolalar yozuvi yo‘q:
        taqsimot ← boshlang‘ich_taqsimot            # admin qo‘lda kiritadi
    aks holda:
        oxirgi ← tarixdagi eng oxirgi 2-kurs sutkasi (oldingi haftada bo‘lsa ham)
        har bir i-joy uchun: taqsimot[zanjir[i+1]] ← oxirgi sutkada zanjir[i] dagi guruh

    band ← ∅
    har bir o‘g‘il joyi J (zanjir tartibida) va Qizlar yotoqxonasi uchun:
        hovuz ← J o‘g‘il joyi bo‘lsa: taqsimot[J] guruhining o‘g‘il kursantlari
                 aks holda: barcha 13 qiz
        # 2-daraja: kim
        nomzodlar ← hovuzdan chiqarib tashlanadi:
                    faol emas | sababli yo‘q | bugun band | kecha (sana−1) naryadda bo‘lgan
        nomzodlar saralanadi kalit(k) bo‘yicha (3-bo‘lim)
        tanlangan ← birinchi min(J.hajm, |nomzodlar|) kishi
        band ← band ∪ tanlangan
        # lavozimlar
        joylashuv ← assign_roles(tanlangan, J.o‘rinlari[:|tanlangan|])
        agar |tanlangan| < J.hajm:
            qolgan o‘rinlar (oxirgi posbonlar) BO‘SH qoladi
            ogohlantirish: "… N ta o‘rin bo‘sh qoldi, admin qo‘lda to‘ldiradi"

    qaytar DayResult(taqsimot, 20 o‘rin (bo‘shlari bilan), ogohlantirishlar, tafsilotlar)
```

`week_bounds(sana)` — sutka tushgan haftaning chegarasi: `sana` dan oldingi (yoki o‘sha) yakshanba 18:00 → keyingi yakshanba 18:00. Yakshanba sanali sutka (yakshanba 18:00 da boshlanadi) yangi haftaning 1-sutkasi.

## 3. Saralash kaliti (guruh ichida yoki qizlar hovuzida)

Har nomzod uchun quyidagi kortej hisoblanadi va **kichigi oldin** tanlanadi:

| № | Kalit | Ma’nosi |
|---|---|---|
| 1 | `haftadagi_soni` | Shu 2-kurs haftasida (yakshanba 18:00 dan) necha marta turgan. Qat’iy: 0 lar tugamaguncha 1 lar olinmaydi → “hamma bir marta turmaguncha hech kim ikkinchi marta tushmaydi” |
| 2 | `jami + jarima` | Butun tarixdagi naryadlar soni; oxirgi naryadi ham shu joy bo‘lsa +1 |
| 3 | `oxirgisi_shu_joy` | Oxirgi naryadi shu joy bo‘lganlar orqaga (0 yoki 1) |
| 4 | `shu_joyda_soni` | Shu joyda necha marta turgan — kam turgan oldin |
| 5 | `oxirgi_sana` | Oxirgi naryad sanasi — uzoqroq dam olgan oldin (hech turmagan — eng oldin) |
| 6 | `tasodif` | `sha256("YYYY-MM-DD|kursant_id")` — alifbo emas, lekin bir xil kirishda doim bir xil |

**Lavozimlar (`assign_roles`).** Tanlangan 2–4 kishining barcha joylashuvlari (ko‘pi bilan 4! = 24 ta) ko‘rib chiqiladi, yig‘indisi eng kichik bo‘lgan variant olinadi:
1. oxirgi lavozimi takrorlanadigan kursantlar soni (masalan, oxirgi naryadida navbatchi bo‘lgan yana navbatchi bo‘lmasin);
2. har kimning **shu joydagi shu lavozimda** turgan sonlari yig‘indisi;
3. har kimning **umuman shu lavozimda** turgan sonlari yig‘indisi.

Teng bo‘lsa — tanlanish tartibidagi birinchi variant. Kursant o‘rinlardan kam bo‘lsa, yuqori lavozimlar (navbatchi, yordamchi) birinchi to‘ldiriladi, oxirgi posbon o‘rinlari bo‘sh qoladi.

## 4. Qat’iy cheklovlar

- **Naryaddan ozod kursantlar** (komandirlar va kurs lavozimlari, CLAUDE.md 2-bo‘lim) nomzodlar hovuziga umuman kirmaydi: `services.engine_cadets()` ularni algoritmga bermaydi, almashtirish oynasida ular “naryaddan ozod — lavozimi” sababi bilan tanlab bo‘lmaydigan qilib ko‘rsatiladi. Algoritmning o‘zi (`naryad/engine/`) va saralash kaliti o‘zgarmagan.
- Faol emas va sababli (kasal, ta’til) kursantlar olinmaydi.
- Bir kursant bir sutkada faqat bitta o‘rinda.
- **Kecha naryadda bo‘lgan kursant bugun olinmaydi.** Boshqa odam qolmasa ham olinmaydi: o‘rin **bo‘sh** qoladi va ogohlantirish chiqadi, o‘rnini admin qo‘lda to‘ldiradi.

> ⚠️ **Qoida o‘zgarishi.** CLAUDE.md 4-D da avval “boshqa odam qolmasa — ogohlantirish bilan olinadi” deyilgan edi. 2-bosqich topshirig‘iga ko‘ra endi o‘rin bo‘sh qoldiriladi. CLAUDE.md 4-D va 10-bo‘lim (13-band) shunga moslab yangilandi.

Hisob bo‘yicha oddiy holatda bu bo‘lmaydi: ketma-ket ikki sutkada bir guruhdan ko‘pi bilan 4 + 3 = 7 kishi kerak, eng kichik guruhda naryadga chiqadigan 11 o‘g‘il bor (YuP-125, ozodlarsiz). Bo‘sh o‘rin faqat bir vaqtda ko‘p kursant sababli yo‘q bo‘lganda chiqadi. Bu `tests/test_exempt.py` da 12 ta 2-kurs haftasi (84 sutka) bo‘yicha tekshirilgan: bo‘sh o‘rin yo‘q, har haftada har guruh ichida farq ≤ 1.

> **Ozoddan qaytgan kursant.** Lavozimdan bo‘shab, qayta naryadga qo‘shilgan kursantning shu haftadagi va jami naryadlari guruhdoshlarinikidan kam bo‘ladi. Saralash kaliti (avval haftadagi soni, keyin jami) uni **avtomatik ravishda birinchi navbatga** qo‘yadi va u guruh o‘rtachasiga yetguncha tez-tez tushadi. Bu **kutilgan xatti-harakat**: adolat jami naryadlar bo‘yicha o‘lchanadi. Bir haftada ko‘pi bilan bitta ortiqcha naryad qoidasi (haftalik farq ≤ 1) baribir saqlanadi, kecha naryadda bo‘lgan kursant bugun olinmaydi. Shu sabab uning jami hisobi bir necha haftada guruhnikiga yetib boradi. Agar buni yumshatish kerak bo‘lsa (masalan, qaytganida jami hisobni guruh o‘rtachasiga tenglashtirish), bu alohida qaror talab qiladi (CLAUDE.md 10-bo‘lim).

## 5. Namunaviy hisob: 18-sentabr tarixi → 19, 20, 21-sentabr

Tarix sifatida faqat `docs/Naryad_tartiblangan.docx` dagi 18-sentabr ro‘yxati bor (hafta 2026-09-13 yakshanba 18:00 da boshlangan; 13–17-sentabr ma’lumoti yo‘q). Har tuzilgan sutka “tasdiqlangan” deb tarixga qo‘shiladi. Ismlar rasmiy ro‘yxat bo‘yicha (Mexmonov, Yuldoshov, Maxmudova).

E’tibor bering:
- 19-sentabrda har guruh zanjirda bir qadam surildi: 18-sentabrda 1-NO‘J da turgan BI-525 → 2-NO‘J, Patruldagi YuP-125 → Markaz va h.k.
- 18-sentabrda turgan 20 kishining hech biri 19-sentabrda yo‘q (kecha naryadda bo‘lgan).
- 20-sentabr — yakshanba, ya’ni **yangi hafta**: “haftadagi soni” noldan boshlanadi, lekin zanjir 19-sentabrdan davom etadi.


| Lavozim | F.I.Sh. | Guruh |
|---|---|---|
| Markaz bo‘yicha navbatchi yordamchisi | G‘ayratov G‘ | BI-625 |
| **1-NO‘J bo‘yicha** | | |
| 1-NO‘J bo‘yicha navbatchi | Sa’dullayev B | BI-525 |
| 1-NO‘J bo‘yicha navbatchi yordamchisi | Maxsudov H | BI-525 |
| 1-NO‘J bo‘yicha posbon | Aslonov A | BI-525 |
| 1-NO‘J bo‘yicha posbon | Yuldoshov M | BI-525 |
| **2-NO‘J bo‘yicha** | | |
| 2-NO‘J bo‘yicha navbatchi | G‘iyozov I | BI-425 |
| 2-NO‘J bo‘yicha posbon | Safarov M | BI-425 |
| 2-NO‘J bo‘yicha posbon | Mirzakarimov O | BI-425 |
| **1-Yotoqxona bo‘yicha** | | |
| Kurs bo‘yicha navbatchi | Ozodov A | BI-225 |
| Kurs bo‘yicha posbon | Shodiyev R | BI-225 |
| Kurs bo‘yicha posbon | Umirov Y | BI-225 |
| **O‘quv binosi bo‘yicha** | | |
| O‘quv binosi bo‘yicha navbatchi | Xudoyberdiyev R | BI-325 |
| O‘quv binosi bo‘yicha posbon | Shavkatov Sh | BI-325 |
| **Institut bo‘yicha patrul** | | |
| Institut bo‘yicha patrul | Kazaxbayev A | YuP-125 |
|  | Kukanov A | YuP-125 |
|  | Mexmonov Sh | YuP-125 |
|  | Hakimjonov A | YuP-125 |
| **Qizlar yotoqxonasi bo‘yicha** | | |
| Qizlar yotoqxonasi bo‘yicha navbatchi | Panjiyeva M | BI-425 |
| Qizlar yotoqxonasi bo‘yicha posbon | Zoirova S | BI-325 |
| Qizlar yotoqxonasi bo‘yicha posbon | Maxmudova H | BI-625 |

### 2026-yil 19-sentabr kunidan 20-sentabr kuniga (shanba, hafta 2026-09-13 dan)

Guruhlar: Markaz bo‘yicha — YuP-125, 1-NO‘J bo‘yicha — BI-625, 2-NO‘J bo‘yicha — BI-525, 1-Yotoqxona bo‘yicha — BI-425, O‘quv binosi bo‘yicha — BI-225, Institut bo‘yicha patrul — BI-325

| Lavozim | F.I.Sh. | Guruh |
|---|---|---|
| Markaz bo‘yicha navbatchi yordamchisi | Sharipov M | YuP-125 |
| **1-NO‘J bo‘yicha** | | |
| 1-NO‘J bo‘yicha navbatchi | Narzullayev O | BI-625 |
| 1-NO‘J bo‘yicha navbatchi yordamchisi | Parpiboyev B | BI-625 |
| 1-NO‘J bo‘yicha posbon | Tursunmurodov B | BI-625 |
| 1-NO‘J bo‘yicha posbon | Avazbayev M | BI-625 |
| **2-NO‘J bo‘yicha** | | |
| 2-NO‘J bo‘yicha navbatchi | Bobomurodov A | BI-525 |
| 2-NO‘J bo‘yicha posbon | A’zamov A | BI-525 |
| 2-NO‘J bo‘yicha posbon | Gulliyev Sh | BI-525 |
| **1-Yotoqxona bo‘yicha** | | |
| Kurs bo‘yicha navbatchi | Aslonov A | BI-425 |
| Kurs bo‘yicha posbon | Karimjonov A | BI-425 |
| Kurs bo‘yicha posbon | Nazarov T | BI-425 |
| **O‘quv binosi bo‘yicha** | | |
| O‘quv binosi bo‘yicha navbatchi | Orziqulov J | BI-225 |
| O‘quv binosi bo‘yicha posbon | Bo‘riyev Sh | BI-225 |
| **Institut bo‘yicha patrul** | | |
| Institut bo‘yicha patrul | Begzodxonov B | BI-325 |
|  | Xayrillayev J | BI-325 |
|  | Abdusaidov M | BI-325 |
|  | Botirov Sh | BI-325 |
| **Qizlar yotoqxonasi bo‘yicha** | | |
| Qizlar yotoqxonasi bo‘yicha navbatchi | Muxammadiyeva X | BI-625 |
| Qizlar yotoqxonasi bo‘yicha posbon | Quvatova D | BI-225 |
| Qizlar yotoqxonasi bo‘yicha posbon | Karimova Sh | BI-225 |

### 2026-yil 20-sentabr kunidan 21-sentabr kuniga (yakshanba, hafta 2026-09-20 dan)

Guruhlar: Markaz bo‘yicha — BI-325, 1-NO‘J bo‘yicha — YuP-125, 2-NO‘J bo‘yicha — BI-625, 1-Yotoqxona bo‘yicha — BI-525, O‘quv binosi bo‘yicha — BI-425, Institut bo‘yicha patrul — BI-225

| Lavozim | F.I.Sh. | Guruh |
|---|---|---|
| Markaz bo‘yicha navbatchi yordamchisi | Suyunov A | BI-325 |
| **1-NO‘J bo‘yicha** | | |
| 1-NO‘J bo‘yicha navbatchi | Axmadaliyev J | YuP-125 |
| 1-NO‘J bo‘yicha navbatchi yordamchisi | Tojiyev Sh | YuP-125 |
| 1-NO‘J bo‘yicha posbon | Oblaberdiyev I | YuP-125 |
| 1-NO‘J bo‘yicha posbon | Abduhamidov A | YuP-125 |
| **2-NO‘J bo‘yicha** | | |
| 2-NO‘J bo‘yicha navbatchi | Mahmudov S | BI-625 |
| 2-NO‘J bo‘yicha posbon | Muxammadjonov A | BI-625 |
| 2-NO‘J bo‘yicha posbon | Mustayev A | BI-625 |
| **1-Yotoqxona bo‘yicha** | | |
| Kurs bo‘yicha navbatchi | Raximov S | BI-525 |
| Kurs bo‘yicha posbon | Sirojov Q | BI-525 |
| Kurs bo‘yicha posbon | Niyozov U | BI-525 |
| **O‘quv binosi bo‘yicha** | | |
| O‘quv binosi bo‘yicha navbatchi | Bayirov A | BI-425 |
| O‘quv binosi bo‘yicha posbon | Rahmonov S | BI-425 |
| **Institut bo‘yicha patrul** | | |
| Institut bo‘yicha patrul | Shermamatov D | BI-225 |
|  | Eshmatov J | BI-225 |
|  | Valiyev J | BI-225 |
|  | Bayozov B | BI-225 |
| **Qizlar yotoqxonasi bo‘yicha** | | |
| Qizlar yotoqxonasi bo‘yicha navbatchi | Shamsiddinova R | YuP-125 |
| Qizlar yotoqxonasi bo‘yicha posbon | Abdullayeva M | BI-225 |
| Qizlar yotoqxonasi bo‘yicha posbon | Ordabaeva M | BI-625 |

### 2026-yil 21-sentabr kunidan 22-sentabr kuniga (dushanba, hafta 2026-09-20 dan)

Guruhlar: Markaz bo‘yicha — BI-225, 1-NO‘J bo‘yicha — BI-325, 2-NO‘J bo‘yicha — YuP-125, 1-Yotoqxona bo‘yicha — BI-625, O‘quv binosi bo‘yicha — BI-525, Institut bo‘yicha patrul — BI-425

| Lavozim | F.I.Sh. | Guruh |
|---|---|---|
| Markaz bo‘yicha navbatchi yordamchisi | Ashuraliyev B | BI-225 |
| **1-NO‘J bo‘yicha** | | |
| 1-NO‘J bo‘yicha navbatchi | Uzaqbergenov A | BI-325 |
| 1-NO‘J bo‘yicha navbatchi yordamchisi | Akramjonov A | BI-325 |
| 1-NO‘J bo‘yicha posbon | Ismoilov S | BI-325 |
| 1-NO‘J bo‘yicha posbon | Saloxitdinov H | BI-325 |
| **2-NO‘J bo‘yicha** | | |
| 2-NO‘J bo‘yicha navbatchi | Latifjanov E | YuP-125 |
| 2-NO‘J bo‘yicha posbon | Shavkatov Y | YuP-125 |
| 2-NO‘J bo‘yicha posbon | Badriyev A | YuP-125 |
| **1-Yotoqxona bo‘yicha** | | |
| Kurs bo‘yicha navbatchi | Abdusattarov B | BI-625 |
| Kurs bo‘yicha posbon | Xaitov A | BI-625 |
| Kurs bo‘yicha posbon | Raximov E | BI-625 |
| **O‘quv binosi bo‘yicha** | | |
| O‘quv binosi bo‘yicha navbatchi | Turdimurodov K | BI-525 |
| O‘quv binosi bo‘yicha posbon | Tursunov S | BI-525 |
| **Institut bo‘yicha patrul** | | |
| Institut bo‘yicha patrul | Abduqahhorov M | BI-425 |
|  | Islomxonov R | BI-425 |
|  | Muxtoxiddinov M | BI-425 |
|  | Sayliyev M | BI-425 |
| **Qizlar yotoqxonasi bo‘yicha** | | |
| Qizlar yotoqxonasi bo‘yicha navbatchi | Abduvaliyeva R | YuP-125 |
| Qizlar yotoqxonasi bo‘yicha posbon | Mamirova M | BI-325 |
| Qizlar yotoqxonasi bo‘yicha posbon | Azizova S | BI-625 |

Quyidagi ikki jadvalda barcha nomzodlarning kalitlari 0 ga teng, chunki tarixda faqat bitta sutka (18-sentabr) bor va u kungi kursantlar “kecha naryadda bo‘lgan” deb chiqarilgan. Bunday holatda tanlovni deterministik tasodif hal qiladi. Tarix to‘planganda kalitlar qanday ishlashi oxirgi jadvalda (2-aylanish) ko‘rinadi.

### Nima uchun aynan shu kursantlar: 19-sentabr, 2-NO‘J bo‘yicha

Guruh: **BI-525**, joy: **2-NO‘J bo‘yicha** (3 o‘rin).

| # | Kursant | Haftadagi soni | Jami | Jarima (oxirgisi shu joy) | Shu joyda | Oxirgi naryad | Tasodif (sha256) | Natija |
|---|---|---|---|---|---|---|---|---|
| 1 | Bobomurodov A | 0 | 0 | 0 | 0 | — | `343b24d1` | ✅ Navbatchi |
| 2 | A’zamov A | 0 | 0 | 0 | 0 | — | `3d61c183` | ✅ Posbon |
| 3 | Gulliyev Sh | 0 | 0 | 0 | 0 | — | `5018a08d` | ✅ Posbon |
| 4 | Ismoiljonov I | 0 | 0 | 0 | 0 | — | `55d44ad2` | — |
| 5 | Nekmurodov F | 0 | 0 | 0 | 0 | — | `b27053aa` | — |
| 6 | Sirojov Q | 0 | 0 | 0 | 0 | — | `c265746e` | — |
| 7 | Niyozov U | 0 | 0 | 0 | 0 | — | `c36f6817` | — |
| 8 | Raximov S | 0 | 0 | 0 | 0 | — | `d98c329e` | — |
| 9 | Tursunov S | 0 | 0 | 0 | 0 | — | `e66fd243` | — |
| 10 | Qodirjanov Sh | 0 | 0 | 0 | 0 | — | `e8ad342f` | — |
| 11 | Nosirjonov A | 0 | 0 | 0 | 0 | — | `eb8d08ba` | — |
| 12 | Turdimurodov K | 0 | 0 | 0 | 0 | — | `f651d332` | — |
| 13 | Abdulazizov O | 0 | 0 | 0 | 0 | — | `fd8f3789` | — |
| ✖ | Aslonov A | | | | | | | chiqarildi: kecha naryadda bo‘lgan |
| ✖ | Maxsudov H | | | | | | | chiqarildi: kecha naryadda bo‘lgan |
| ✖ | Yuldoshov M | | | | | | | chiqarildi: kecha naryadda bo‘lgan |
| ✖ | Sa’dullayev B | | | | | | | chiqarildi: kecha naryadda bo‘lgan |

### Nima uchun aynan shu qizlar: 19-sentabr, Qizlar yotoqxonasi

Guruh: **qizlar**, joy: **Qizlar yotoqxonasi bo‘yicha** (3 o‘rin).

| # | Kursant | Haftadagi soni | Jami | Jarima (oxirgisi shu joy) | Shu joyda | Oxirgi naryad | Tasodif (sha256) | Natija |
|---|---|---|---|---|---|---|---|---|
| 1 | Muxammadiyeva X | 0 | 0 | 0 | 0 | — | `2338a6d9` | ✅ Navbatchi |
| 2 | Quvatova D | 0 | 0 | 0 | 0 | — | `405fd2d4` | ✅ Posbon |
| 3 | Karimova Sh | 0 | 0 | 0 | 0 | — | `640240a5` | ✅ Posbon |
| 4 | Ordabaeva M | 0 | 0 | 0 | 0 | — | `6b589894` | — |
| 5 | Abdullayeva M | 0 | 0 | 0 | 0 | — | `7bec0e4d` | — |
| 6 | Abduvaliyeva R | 0 | 0 | 0 | 0 | — | `9f2c2abc` | — |
| 7 | Baxtiyorova N | 0 | 0 | 0 | 0 | — | `b76b3b8f` | — |
| 8 | Mamirova M | 0 | 0 | 0 | 0 | — | `d0201209` | — |
| 9 | Shamsiddinova R | 0 | 0 | 0 | 0 | — | `f3433574` | — |
| 10 | Azizova S | 0 | 0 | 0 | 0 | — | `f676d323` | — |
| ✖ | Zoirova S | | | | | | | chiqarildi: kecha naryadda bo‘lgan |
| ✖ | Panjiyeva M | | | | | | | chiqarildi: kecha naryadda bo‘lgan |
| ✖ | Maxmudova H | | | | | | | chiqarildi: kecha naryadda bo‘lgan |

Adolat jadvali uchun keyingi 2-kurs haftasi (27-sentabr – 4-oktabr, 21-sentabrdan 6 kun keyin) yuqoridagi tarix ustiga to‘liq 7 sutka qilib tuzildi.

### 7 sutkalik adolat jadvali: hafta 2026-09-27 (yakshanba) – 2026-10-04

| Hovuz | Kishi | Haftadagi o‘rinlar | 1 marta | 2 marta | 3+ marta | min | max | Farq (max−min) |
|---|---|---|---|---|---|---|---|---|
| BI-225 | 14 | 21 | 7 | 7 | 0 | 1 | 2 | **1** |
| BI-325 | 14 | 20 | 8 | 6 | 0 | 1 | 2 | **1** |
| BI-425 | 15 | 18 | 12 | 3 | 0 | 1 | 2 | **1** |
| BI-525 | 17 | 21 | 13 | 4 | 0 | 1 | 2 | **1** |
| BI-625 | 14 | 19 | 9 | 5 | 0 | 1 | 2 | **1** |
| YuP-125 | 13 | 20 | 6 | 7 | 0 | 1 | 2 | **1** |
| Qizlar (13) | 13 | 21 | 5 | 8 | 0 | 1 | 2 | **1** |

Guruhlar aylanishi:

| Sutka | Markaz bo‘yicha | 1-NO‘J bo‘yicha | 2-NO‘J bo‘yicha | 1-Yotoqxona bo‘yicha | O‘quv binosi bo‘yicha | Institut bo‘yicha patrul |
|---|---|---|---|---|---|---|
| 27-sentabr | BI-425 | BI-225 | BI-325 | YuP-125 | BI-625 | BI-525 |
| 28-sentabr | BI-525 | BI-425 | BI-225 | BI-325 | YuP-125 | BI-625 |
| 29-sentabr | BI-625 | BI-525 | BI-425 | BI-225 | BI-325 | YuP-125 |
| 30-sentabr | YuP-125 | BI-625 | BI-525 | BI-425 | BI-225 | BI-325 |
| 1-oktabr | BI-325 | YuP-125 | BI-625 | BI-525 | BI-425 | BI-225 |
| 2-oktabr | BI-225 | BI-325 | YuP-125 | BI-625 | BI-525 | BI-425 |
| 3-oktabr | BI-425 | BI-225 | BI-325 | YuP-125 | BI-625 | BI-525 |

Bu jadvalda YuP-125 (13 o‘g‘il) haftaning 5-sutkasida 1-NO‘J ga 4 kishi beradi, lekin shu haftada turmaganlardan faqat 3 kishi qolgan. Shuning uchun 4-o‘ringa “haftadagi soni = 1” bo‘lganlar ichidan **jami eng kam** (1) bo‘lgan Abduqodirov A olindi; qolganlarida jami 2. Abduhamidov A kecha turgani uchun chiqarildi.

### Nima uchun aynan shu kursantlar (2-aylanish): 1-oktabr, 1-NO‘J bo‘yicha

Guruh: **YuP-125**, joy: **1-NO‘J bo‘yicha** (4 o‘rin).

| # | Kursant | Haftadagi soni | Jami | Jarima (oxirgisi shu joy) | Shu joyda | Oxirgi naryad | Tasodif (sha256) | Natija |
|---|---|---|---|---|---|---|---|---|
| 1 | Badriyev A | 0 | 1 | 0 | 0 | 2026-09-21 | `2d90bdd8` | ✅ Navbatchi |
| 2 | Latifjanov E | 0 | 1 | 0 | 0 | 2026-09-21 | `72de4a00` | ✅ Posbon |
| 3 | Shavkatov Y | 0 | 1 | 0 | 0 | 2026-09-21 | `7a587d45` | ✅ Navbatchi yordamchisi |
| 4 | Abduqodirov A | 1 | 1 | 0 | 0 | 2026-09-27 | `c7317dde` | ✅ Posbon |
| 5 | Mexmonov Sh | 1 | 2 | 0 | 0 | 2026-09-27 | `9bfcd509` | — |
| 6 | Kazaxbayev A | 1 | 2 | 0 | 0 | 2026-09-27 | `c53585ae` | — |
| 7 | Hakimjonov A | 1 | 2 | 0 | 0 | 2026-09-28 | `719842f7` | — |
| 8 | Kukanov A | 1 | 2 | 0 | 0 | 2026-09-28 | `750faa58` | — |
| 9 | Sharipov M | 1 | 2 | 0 | 0 | 2026-09-29 | `08a23e4b` | — |
| 10 | Tojiyev Sh | 1 | 2 | 0 | 1 | 2026-09-29 | `786383a6` | — |
| 11 | Oblaberdiyev I | 1 | 2 | 0 | 1 | 2026-09-29 | `b558dd10` | — |
| 12 | Axmadaliyev J | 1 | 2 | 0 | 1 | 2026-09-29 | `faf335c1` | — |
| ✖ | Abduhamidov A | | | | | | | chiqarildi: kecha naryadda bo‘lgan |

Ro'yxat: 100 kursant (87 o‘g‘il, 13 qiz).

## 6. Uzoq muddatli kuzatuv (12 ta 2-kurs haftasi, 84 sutka)

Testdan tashqari tekshiruv: bo‘sh tarixdan 12 hafta (har biri 14 kun oralig‘ida) ketma-ket tuzildi.

| Ko‘rsatkich | Natija |
|---|---|
| Ogohlantirish / bo‘sh o‘rin | 0 |
| Har hafta ichida guruhdagi min/max farqi | doim ≤ 1 |
| 12 hafta jamida guruhdagi min/max farqi | 1–2 (masalan, BI-525: 13–15, YuP-125: 18–19) |
| Bir kursantning bitta joyda eng ko‘p turgani | 4–6 marta (jami 13–19 naryaddan; ideal ≈ 3) |
| Qizlarda navbatchi lavozimi (12 haftada) | har qizga 5–7 marta |

Bir joyga tushish soni idealdan biroz yuqori. Sababi: haftalik qat’iy navbat va sutkama-sutka tuzish kursant qaysi kuni (demak qaysi joyda) turishini ko‘p jihatdan belgilab qo‘yadi. Kalitda “shu joyda soni” ni yuqoriga ko‘chirib ko‘rdim — sezilarli yaxshilanish bermadi, shuning uchun topshiriqdagi tartib saqlandi (8-bo‘lim, 2-savol).

## 7. Testlar (`tests/test_allocator.py`, 32 ta)

| Tekshiriladigan qoida | Test |
|---|---|
| Hafta yakshanba 18:00 – yakshanba 18:00 | `test_week_start`, `test_week_bounds_is_sunday_18_to_sunday_18` |
| Tarix bo‘lmasa boshlang‘ich taqsimot shart | `test_rotation_requires_initial_mapping_without_history` |
| Har guruh har sutka zanjirda keyingi joyga o‘tadi | `test_rotation_moves_each_group_to_next_post` |
| Guruh ketma-ket ikki sutka bir joyga tushmaydi | `test_group_never_same_post_two_days_in_row` |
| 6 sutkada har guruh har joyni bir martadan o‘taydi | `test_six_days_each_group_visits_each_post_once` |
| Zanjir keyingi haftaga davom etadi | `test_rotation_continues_into_next_week` |
| Har sutka aynan 20 kishi, kursant bitta o‘rinda | `test_every_day_has_exactly_20_people` |
| Har joy bitta guruhdan | `test_each_post_is_filled_by_one_group` |
| Qizlar faqat Qizlar yotoqxonasida | `test_girls_only_in_girls_dormitory` |
| Hamma bir marta turmaguncha hech kim ikkinchi marta yo‘q (o‘g‘illar va qizlar) | `test_nobody_twice_before_everyone_once` |
| Kursant ikki sutka ketma-ket tushmaydi | `test_nobody_two_days_in_a_row` |
| 7 sutkada guruh ichida min/max farqi ≤ 1 | `test_week_fairness_min_max_difference_at_most_one` |
| 2 haftada ham adolat va to‘liqlik | `test_two_weeks_fairness_and_no_post_repeat_streaks` |
| Sababli kursant tanlanmaydi | `test_absent_cadet_is_not_selected` |
| Faol emas kursant tanlanmaydi | `test_inactive_cadet_is_not_selected` |
| Odam yetmasa — o‘rin bo‘sh, ogohlantirish bor, kechagilar olinmaydi | `test_slot_left_empty_with_warning_when_only_yesterdays_cadets_remain` |
| Oxirgi lavozim takrorlanmaydi | `test_assign_roles_avoids_repeating_last_role`, `test_roles_rotate_in_simulation` |
| Deterministik (ro‘yxat tartibi o‘zgarsa ham natija bir xil) | `test_same_input_same_output` |
| Qisqa shakl va apostroflar | `test_short_name` (7 holat), `test_normalize_apostrophes` |
| Ro‘yxat CLAUDE.md 2-bo‘lim bilan mos | `test_roster_matches_claude_md` |

## 8. Ishga tushirish

```bash
# loyiha ildizida, Python 3.12
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

pytest                              # 32 passed
python scripts/demo.py              # 5-bo‘limdagi jadvallarni chiqaradi
python scripts/build_roster.py      # roster.json ni .doc dan qayta yaratish (LibreOffice kerak)
```

## 9. Ochiq savollar

1. **20–21-sentabr demosi va haftalar navbati.** Kurslar haftama-hafta almashadi, ya’ni 20-sentabrdan boshlangan hafta aslida boshqa kursniki. Demo topshiriq bo‘yicha 20–21-sentabrni yangi 2-kurs haftasi deb hisobladi. *Tavsiya:* 3-bosqichda (Django) sutkani faqat ochilgan 2-kurs haftasi (`duty_week`) ichida tuzishga ruxsat berish; algoritmning o‘zi esa sanani tekshirmaydi.
2. **Bir joyga takror tushish (6-bo‘lim).** 12 haftada kursant bitta joyda 4–6 marta turishi mumkin (ideal ≈ 3). *Tavsiya:* hozircha shu holicha qoldirish va statistika bosqichida haqiqiy ma’lumotda kuzatish; kerak bo‘lsa, keyin kalitga “oxirgi 2 naryadi shu joy bo‘lsa — kuchliroq jarima” qo‘shish (4-bo‘limdagi qoidalar o‘zgarmaydi, faqat jarima kuchayadi).
3. **Ro‘yxatdagi g‘alati yozuvlar.** `Bayozov Baxtiyor Po‘Lotovich` (katta L) va `Tursunmurodov Bahodir Xon Turdialijonovich` (ism “Bahodir Xon” deb olindi). *Tavsiya:* rasmiy yozuvni o‘zgartirmaslik (10-bo‘lim, 2-band); kerak bo‘lsa, admin keyin interfeysda tuzatadi.
4. **GitHub’ga push.** `sutkalik-naryad` repozitoriyasiga hali yozish huquqi yo‘q, `West-hackaton` ga esa taqiqlangan. O‘zgarishlar mahalliy git’ga commit qilindi va zip qilib berildi; ruxsat berilgach, butun tarix bilan push qilinadi.
