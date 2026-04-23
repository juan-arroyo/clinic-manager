# backend/apps/reports/urls.py
# URLs del módulo de reportes.

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Página principal de reportes con filtros y gráficos
    path('', views.reports_view, name='index'),

    # Exportación a Excel de todas las ventas
    path('excel/ventas/', views.export_sales_excel, name='export_sales'),

    # Exportación a Excel de solo las facturas emitidas
    path('excel/facturas/', views.export_invoices_excel, name='export_invoices'),

    # Exportación a Excel filtrado por fisioterapeuta
    path('excel/fisio/', views.export_fisio_excel, name='export_fisio'),
]