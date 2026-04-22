# backend/config/settings/dev.py
# Configuración específica de desarrollo.
# Importa todo de base.py y sobreescribe lo necesario.

from .base import *  # importamos toda la configuración base

# En desarrollo, DEBUG=True muestra errores detallados en el navegador
DEBUG = True

# En desarrollo aceptamos peticiones desde localhost y la red local
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '192.168.1.108']

# Dominios de confianza para CSRF — importante cuando usamos Docker + Nginx
# (lección aprendida del proyecto anterior)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    'http://192.168.1.108',
]