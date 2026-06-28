FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt daphne

COPY . .

RUN mkdir -p staticfiles media static

EXPOSE 8001

CMD ["daphne", "-b", "0.0.0.0", "-p", "8001", "config.asgi:application"]
