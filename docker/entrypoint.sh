#!/bin/sh
# Konteyner ishga tushganda: migratsiyalar, so'ng gunicorn.
set -e

python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --timeout "${GUNICORN_TIMEOUT:-60}" \
    --max-requests 1000 --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile -
