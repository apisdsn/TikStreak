FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data \
    BROWSER_PATH=/usr/bin/chromium

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium fonts-liberation fonts-noto-color-emoji tzdata tini curl \
    && (apt-get install -y --no-install-recommends chromium-headless-shell || echo 'chromium-headless-shell tidak tersedia di distro ini; memakai Chromium penuh') \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app

VOLUME /data
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fs http://127.0.0.1:8000/api/health || exit 1

ENTRYPOINT ["tini", "--"]
# TRUST_PROXY=1 hanya bila ada reverse proxy tepercaya di depan (lihat .env.example)
CMD ["sh", "-c", "if [ \"$TRUST_PROXY\" = 1 ] || [ \"$TRUST_PROXY\" = true ]; then exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-*}\"; else exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-proxy-headers; fi"]
