# backend/config/settings/prod.py
# Configuración específica de producción.
# Se usará cuando despleguemos en la Raspberry Pi o VPS.

from .base import *        # importamos toda la configuración base
from decouple import config

# En producción, DEBUG=False — nunca mostrar errores internos al usuario
DEBUG = False

# En producción se añadirán los dominios reales aquí
# ALLOWED_HOSTS = config('ALLOWED_HOSTS').split(',')

# Seguridad adicional para producción
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'