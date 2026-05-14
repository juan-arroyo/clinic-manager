# backend/Dockerfile

FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE: evita generar archivos .pyc innecesarios en el contenedor
# PYTHONUNBUFFERED: fuerza salida en tiempo real — imprescindible para ver logs en Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# gcc y libpq-dev: necesarios para compilar psycopg2 (conector Python ↔ PostgreSQL)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt se copia antes que el código para aprovechar la caché de Docker:
# si no cambia, Docker reutiliza la capa y no reinstala dependencias en cada build
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .