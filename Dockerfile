# E-NARYAD (sutkalik naryad platformasi) — bitta image: lokal (docker-compose.yml), server (docker-compose.prod.yml), Railway
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# PDF (WeasyPrint): Pango, HarfBuzz va Liberation shriftlari (Times New Roman bo'lmasa — Liberation Serif).
# Times New Roman: fonts/times.ttf va fonts/timesbd.ttf qo'yilsa, image'ga shu yerdan tushadi (fonts/README.md).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-liberation fontconfig \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Statik fayllar build paytida yig'iladi (WhiteNoise orqali beriladi)
RUN DJANGO_SECRET_KEY=build-only DJANGO_DEBUG=False python manage.py collectstatic --noinput \
    && useradd --create-home --uid 1000 app \
    && mkdir -p /app/logs \
    && chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "docker/entrypoint.sh"]
