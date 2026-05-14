# backend/config/urls.py
# URLs principales del proyecto — cada app gestiona sus propias rutas.

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.users.urls')),
    path('pacientes/', include('apps.patients.urls')),
    path('bonos/', include('apps.bonuses.urls')),
    path('ventas/', include('apps.sales.urls')),
    path('reportes/', include('apps.reports.urls')),
]

# En desarrollo Django sirve los archivos media directamente.
# En producción esta responsabilidad la asume Nginx.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)