# backend/apps/sales/admin.py
# Registra los modelos Sale y FisioRate en el panel de administración.

from django.contrib import admin
from .models import Sale, FisioRate


@admin.register(FisioRate)
class FisioRateAdmin(admin.ModelAdmin):
    # El propietario configura aquí las tarifas de cada fisioterapeuta
    list_display = ['fisio', 'treatment_type', 'is_bonus', 'rate']
    list_filter = ['fisio', 'is_bonus']
    ordering = ['fisio', 'treatment_type']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['date', 'patient', 'amount', 'treatment_type', 'worker', 'payment_method', 'invoice_issued', 'is_paid']
    list_filter = ['invoice_issued', 'is_paid', 'treatment_type', 'payment_method', 'worker']
    search_fields = ['patient__first_name', 'patient__last_name', 'invoice_number', 'description']
    readonly_fields = ['invoice_number', 'fisio_amount', 'created_at']
    date_hierarchy = 'date'  # navegación por fechas en el admin
    ordering = ['-date']