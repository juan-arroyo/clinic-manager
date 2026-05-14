# backend/apps/bonuses/admin.py

from django.contrib import admin
from .models import Bonus


@admin.register(Bonus)
class BonusAdmin(admin.ModelAdmin):
    list_display = ['bonus_number', 'patient', 'bonus_type', 'sessions_used', 'sessions_remaining', 'is_active', 'created_at']
    list_filter = ['is_active', 'bonus_type']
    search_fields = ['bonus_number', 'patient__first_name', 'patient__last_name']
    # bonus_number y sessions_used se gestionan automáticamente — no se editan desde el admin
    readonly_fields = ['bonus_number', 'sessions_used', 'created_at']