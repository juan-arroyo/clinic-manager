# backend/config/wsgi.py
# Punto de entrada para el servidor WSGI (Gunicorn en producción).
# WSGI es el protocolo estándar que conecta Django con el servidor web.

import os
from django.core.wsgi import get_wsgi_application

# Le decimos a Django qué archivo de settings usar
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

application = get_wsgi_application()