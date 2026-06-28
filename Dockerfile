FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# App source
COPY . .

# Create required directories
RUN mkdir -p staticfiles media static

# Collect static files (needs a dummy secret key)
RUN DJANGO_SECRET_KEY=build-time-dummy-key \
    DB_HOST=localhost \
    DB_NAME=dummy \
    DB_USER=dummy \
    DB_PASSWORD=dummy \
    REDIS_URL=redis://localhost:6379/0 \
    python manage.py collectstatic --noinput --ignore=*.pyc 2>/dev/null || true

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
