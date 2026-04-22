# backend/apps/patients/admin.py
# Registra el modelo Patient en el panel de administración.

from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    # Columnas visibles en el listado
    list_display = ['last_name', 'first_name', 'dni', 'phone', 'email', 'registration_date', 'is_active']

    # Filtros laterales
    list_filter = ['is_active', 'registration_date']

    # Búsqueda por estos campos
    search_fields = ['first_name', 'last_name', 'dni', 'phone', 'email']

    # Ordenación por defecto
    ordering = ['last_name', 'first_name']