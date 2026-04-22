# backend/manage.py
# Comando central de Django.
# Se usa para migraciones, runserver, crear apps, etc.

import os
import sys

def main():
    # Apunta a los settings de desarrollo por defecto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("No se pudo importar Django.") from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()