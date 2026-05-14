# backend/apps/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db import models
from django.forms import TextInput
from .models import User, Physio


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'color', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Datos de la clínica', {
            'fields': ('role', 'color')
        }),
    )


@admin.register(Physio)
class PhysioAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'color', 'is_active']
    list_filter = ['is_active']
    search_fields = ['first_name', 'last_name']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        # Reemplaza el input de texto del campo color por un color picker visual
        if db_field.name == 'color':
            kwargs['widget'] = TextInput(attrs={
                'type': 'color',
                'style': 'width:80px; height:40px; padding:2px;'
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)