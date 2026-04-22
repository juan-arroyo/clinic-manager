# backend/config/settings/base.py
# Configuración base compartida por todos los entornos (dev y prod).
# Nunca se usa directamente — siempre se importa desde dev.py o prod.py.

from pathlib import Path
from decouple import config  # lee variables del archivo .env de forma segura

# BASE_DIR apunta a la carpeta /backend, raíz del proyecto Django
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Clave secreta de Django — se lee del .env
SECRET_KEY = config('SECRET_KEY')

# Lista de dominios aceptados — se lee del .env y se convierte en lista
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# --- APLICACIONES INSTALADAS ---
INSTALLED_APPS = [
    # Unfold debe ir ANTES que django.contrib.admin
    'unfold',

    # Apps del núcleo de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías de terceros
    'django_htmx',

    # Nuestras apps (las crearemos en fases posteriores)
    #'apps.users',
    #'apps.patients',
    #'apps.bonuses',
    #'apps.sales',
    #'apps.reports',
]

# --- MIDDLEWARE ---
# Capas de procesamiento que se aplican a cada petición/respuesta, en orden
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',  # necesario para que HTMX funcione
]

# Archivo donde Django busca las URLs principales
ROOT_URLCONF = 'config.urls'

# --- TEMPLATES ---
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # carpeta global de templates
        'APP_DIRS': True,  # busca templates también dentro de cada app
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Punto de entrada para Gunicorn en producción
WSGI_APPLICATION = 'config.wsgi.application'

# --- BASE DE DATOS ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': 'db',       # 'db' es el nombre del servicio en docker-compose.yml
        'PORT': '5432',
    }
}

# --- MODELO DE USUARIO PERSONALIZADO ---
# Debe definirse ANTES de la primera migración (lección aprendida)
#AUTH_USER_MODEL = 'users.User'

# --- CONTRASEÑAS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-es'
TIME_ZONE = config('TIME_ZONE', default='Europe/Madrid')
USE_I18N = True
USE_TZ = True  # usa zonas horarias (importante para fechas correctas)

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']   # estáticos durante desarrollo
STATIC_ROOT = BASE_DIR / 'staticfiles'     # donde collectstatic los reúne para Nginx

# --- ARCHIVOS MEDIA ---
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Tipo de clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- AUTENTICACIÓN ---
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'