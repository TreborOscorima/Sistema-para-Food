# ─── Stage 1: install deps ────────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
COPY _vendor/ _vendor/

RUN pip install --no-cache-dir --prefix=/install /build/_vendor/tuwayki-core 2>/dev/null || true && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt

# Node para Reflex build
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# ─── Stage 2: runtime ─────────────────────────────────────────────────────────
FROM python:3.13-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl nodejs npm libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

COPY . .

RUN chmod +x scripts/docker-entrypoint.sh

EXPOSE 3003 3004

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=prod

ENTRYPOINT ["scripts/docker-entrypoint.sh"]
