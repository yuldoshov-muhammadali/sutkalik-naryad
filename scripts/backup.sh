#!/bin/sh
# PostgreSQL zaxira nusxasi (pg_dump, custom format). docker-compose.prod.yml dagi `backup` servisida ishlaydi.
#
#   Qo'lda (hozir):     docker compose -f docker-compose.prod.yml exec backup sh /scripts/backup.sh
#   Har kuni (servis):  sh /scripts/backup.sh --har-kuni   (BACKUP_TIME da, standart 03:00)
#
# Fayllar: backups/naryad_YYYY-MM-DD_HHMMSS.dump ; BACKUP_KEEP_DAYS (standart 30) kundan eskilari o'chiriladi.
# Ulanish: PGHOST, PGDATABASE, PGUSER, PGPASSWORD muhit o'zgaruvchilari.
set -eu
umask 077  # zaxirada parol xeshlari bor — faqat egasi o‘qiydi

BACKUP_DIR="${BACKUP_DIR:-/backups}"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-30}"
BACKUP_TIME="${BACKUP_TIME:-03:00}"

backup_once() {
    mkdir -p "$BACKUP_DIR"
    stamp="$(date +%Y-%m-%d_%H%M%S)"
    target="$BACKUP_DIR/naryad_${stamp}.dump"
    tmp="$target.tmp"
    if pg_dump --format=custom --no-owner --no-privileges --file="$tmp"; then
        mv "$tmp" "$target"
        echo "$(date '+%F %T') zaxira tayyor: $target ($(du -h "$target" | cut -f1))"
    else
        rm -f "$tmp"
        echo "$(date '+%F %T') XATO: zaxira olinmadi" >&2
        return 1
    fi
    # eski zaxiralarni o'chirish (oxirgi KEEP_DAYS kun saqlanadi)
    find "$BACKUP_DIR" -maxdepth 1 -name 'naryad_*.dump' -type f -mtime "+$((KEEP_DAYS - 1))" -print -delete \
        | sed 's/^/eski zaxira o‘chirildi: /'
}

seconds_until() {
    # keyingi HH:MM gacha necha soniya
    now=$(date +%s)
    next=$(date -d "$(date +%Y-%m-%d) $1" +%s 2>/dev/null || date -D '%Y-%m-%d %H:%M' -d "$(date +%Y-%m-%d) $1" +%s)
    [ "$next" -le "$now" ] && next=$((next + 86400))
    echo $((next - now))
}

if [ "${1:-}" = "--har-kuni" ]; then
    echo "Kunlik zaxira: har kuni $BACKUP_TIME da, $KEEP_DAYS kun saqlanadi ($BACKUP_DIR)."
    while true; do
        wait_s=$(seconds_until "$BACKUP_TIME")
        sleep "$wait_s"
        backup_once || true
        sleep 60
    done
else
    backup_once
fi
