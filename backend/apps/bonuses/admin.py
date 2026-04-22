# backend/apps/bonuses/admin.py
# Registra el modelo Bonus en el panel de administración.

from django.contrib import admin
from .models import Bonus


@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    # Columnas visibles en el listado
    list_display = ['bonus_number', 'patient', 'bonus_type', 'sessions_used', 'sessions_remaining', 'is_active', 'created_at']

    # Filtros laterales
    list_filter = ['is_active', 'bonus_type']

    # Búsqueda
    search_fields = ['bonus_number', 'patient__first_name', 'patient__last_name']

    # Campos de solo lectura — no se pueden editar manualmente
    readonly_fields = ['bonus_number', 'sessions_used', 'created_at']