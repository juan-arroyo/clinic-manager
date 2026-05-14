# backend/config/settings/prod.py
# Configuración específica de producción.

from .base import *
from decouple import config

DEBUG = False

ALLOWED_HOSTS = [
    'clinic.jmarroyo.es',
    'localhost',
    '127.0.0.1',
]

# Cloudflare gestiona HTTPS externamente — Django necesita confiar en la URL pública con https://
CSRF_TRUSTED_ORIGINS = [
    'https://clinic.jmarroyo.es',
    'http://localhost',
    'http://127.0.0.1',
]

# --- SEGURIDAD ---
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'          # protección contra clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True