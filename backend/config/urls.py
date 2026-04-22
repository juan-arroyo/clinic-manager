# backend/config/urls.py
# Mapa central de URLs del proyecto.
# Aquí Django decide qué app maneja cada dirección web.

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static  # para servir archivos media en desarrollo

urlpatterns = [
    # Panel de administración de Django (con Unfold)
    path('admin/', admin.site.urls),

    # URLs del módulo de usuarios (login, logout, perfil)
    path('', include('apps.users.urls')),

    # URLs del módulo de pacientes
    path('pacientes/', include('apps.patients.urls')),

    # Aquí iremos añadiendo las URLs de cada app en fases posteriores
    # path('', include('apps.users.urls')),
    # path('pacientes/', include('apps.patients.urls')),
]

# En desarrollo, Django sirve los archivos media directamente
# En producción lo hace Nginx
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)