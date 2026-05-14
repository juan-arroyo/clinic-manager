# backend/manage.py
# Punto de entrada para comandos de gestión de Django.

import os
import sys


def main():
    # dev.py por defecto para desarrollo local.
    # En producción, docker-compose.yml sobreescribe esto con config.settings.prod
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("No se pudo importar Django.") from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()