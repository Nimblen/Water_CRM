FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements/prod.txt .

RUN pip install --upgrade pip
RUN pip wheel --wheel-dir=/wheels -r prod.txt



FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -r -u 1000 appuser

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements/prod.txt .

RUN pip install --no-cache /wheels/*

COPY . .

RUN chmod +x scripts/*.sh
RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["./scripts/entrypoint.sh"]