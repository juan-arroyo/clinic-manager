# backend/config/wsgi.py
# Punto de entrada para Gunicorn en producción.

import os
from django.core.wsgi import get_wsgi_application

# prod.py por defecto. Si DJANGO_SETTINGS_MODULE ya está definida en el entorno
# (como ocurre en el .env), setdefault no la sobreescribe.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

application = get_wsgi_application()