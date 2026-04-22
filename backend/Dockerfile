# backend/Dockerfile
# Instrucciones para construir el contenedor de Django.
# Docker lee este archivo de arriba a abajo y ejecuta cada instrucción en orden.

# Partimos de la imagen oficial de Python 3.12 en su versión ligera
FROM python:3.12-slim

# Evita que Python genere archivos .pyc (bytecode compilado)
ENV PYTHONDONTWRITEBYTECODE=1

# Fuerza a Python a mostrar los print() y errores en tiempo real (sin buffer)
ENV PYTHONUNBUFFERED=1

# Creamos y nos movemos al directorio de trabajo dentro del contenedor
WORKDIR /app

# Instalamos dependencias del sistema que algunas librerías Python necesitan
# gcc y libpq-dev: necesarios para compilar psycopg2 (conector Python ↔ PostgreSQL)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiamos requirements.txt antes que el resto del código
# Esto aprovecha la caché de Docker: si no cambia, no reinstala todo
COPY requirements.txt .

# Instalamos las librerías Python
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiamos el resto del código al contenedor
COPY . .