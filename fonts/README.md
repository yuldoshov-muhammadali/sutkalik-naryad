# Shriftlar (PDF uchun)

Rasmiy shakl **Times New Roman** shriftida chiqadi (CLAUDE.md 5-bo‘lim). Bu shrift litsenziyali
bo‘lgani uchun repozitoriyga qo‘shilmaydi (`.gitignore`), uni o‘zingiz qo‘yasiz:

1. Windows kompyuterda `C:\Windows\Fonts` papkasini oching.
2. **Times New Roman** (oddiy) va **Times New Roman Bold** fayllarini shu `fonts/` papkaga nusxalang.
3. Fayl nomlari aynan shunday bo‘lsin: `times.ttf` va `timesbd.ttf`.
4. Serverni qayta ishga tushiring (Docker’da — `docker compose up --build`).

Fayllar bo‘lmasa, o‘lchamlari Times New Roman bilan aynan bir xil bo‘lgan **Liberation Serif**
ishlatiladi (Docker image’ga `fonts-liberation` o‘rnatilgan; Linux’da: `apt install fonts-liberation`).
