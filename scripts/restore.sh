#!/bin/sh
# Zaxiradan tiklash (serverda, loyiha papkasida ishga tushiriladi):
#
#   sh scripts/restore.sh backups/naryad_2026-10-13_030000.dump
#
# Nima qiladi: web'ni to'xtatadi → hozirgi bazadan xavfsizlik uchun yana bir zaxira oladi →
# bazani zaxiradagi holatga qaytaradi → migratsiyalarni qo'llaydi → web'ni qayta ishga tushiradi.
set -eu

COMPOSE="docker compose -f docker-compose.prod.yml"
FILE="${1:-}"

if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "Foydalanish: sh scripts/restore.sh backups/naryad_YYYY-MM-DD_HHMMSS.dump"
    echo "Mavjud zaxiralar:"
    ls -1t backups/naryad_*.dump 2>/dev/null | head -10 || echo "  (yo‘q)"
    exit 1
fi

if [ "${2:-}" != "--ha" ]; then
    printf "DIQQAT: hozirgi baza %s holatiga qaytariladi. Davom etasizmi? (ha/yo‘q): " "$FILE"
    read -r answer
    [ "$answer" = "ha" ] || { echo "Bekor qilindi."; exit 1; }
fi

echo "1/5 web to‘xtatilmoqda…"
$COMPOSE stop web

echo "2/5 hozirgi bazadan xavfsizlik zaxirasi olinmoqda…"
$COMPOSE exec -T backup sh /scripts/backup.sh

echo "3/5 baza tiklanmoqda: $FILE"
$COMPOSE exec -T db sh -c 'pg_restore --clean --if-exists --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$FILE"

echo "4/5 web ishga tushirilmoqda (migratsiyalar avtomatik)…"
$COMPOSE start web

echo "5/5 tekshirilmoqda…"
for i in $(seq 1 30); do
    if $COMPOSE exec -T web python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=5).status == 200 else 1)" 2>/dev/null; then
        echo "Tayyor: baza $FILE holatiga qaytarildi."
        exit 0
    fi
    sleep 2
done
echo "XATO: web javob bermayapti — loglarni ko‘ring: $COMPOSE logs web" >&2
exit 1
