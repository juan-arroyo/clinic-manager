# backend/apps/patients/admin.py

from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['last_name', 'first_name', 'dni', 'phone', 'email', 'registration_date', 'is_active']
    list_filter = ['is_active', 'registration_date']
    search_fields = ['first_name', 'last_name', 'dni', 'phone', 'email']
    ordering = ['last_name', 'first_name']