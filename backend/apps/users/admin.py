# backend/apps/users/admin.py
# Registra el modelo User en el panel de administración de Django.

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Campos que se muestran en el listado de usuarios
    list_display = ['email', 'first_name', 'last_name', 'role', 'color', 'is_active']

    # Campos por los que se puede filtrar
    list_filter = ['role', 'is_active']

    # Añadimos nuestros campos personalizados al formulario de edición
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Datos de la clínica', {
            'fields': ('role', 'color')
        }),
    )