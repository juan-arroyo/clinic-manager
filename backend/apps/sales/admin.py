# backend/apps/sales/admin.py

from django.contrib import admin
from .models import Sale, FisioRate, Invoice


@admin.register(FisioRate)
class FisioRateAdmin(admin.ModelAdmin):
    # El propietario gestiona aquí las tarifas de cada fisioterapeuta
    list_display = ['fisio', 'treatment_type', 'is_bonus', 'rate']
    list_filter = ['fisio', 'is_bonus']
    ordering = ['fisio', 'treatment_type']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['date', 'patient', 'amount', 'treatment_type', 'worker', 'payment_method', 'invoice_issued']
    list_filter = ['invoice_issued', 'treatment_type', 'payment_method', 'worker']
    search_fields = ['patient__first_name', 'patient__last_name', 'invoice_number', 'description']
    readonly_fields = ['invoice_number', 'fisio_amount', 'created_at']
    date_hierarchy = 'date'  # habilita navegación por fecha en el listado del admin
    ordering = ['-date']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['number', 'sale', 'issued_at', 'recipient_email', 'last_sent_at']
    ordering = ['-issued_at']