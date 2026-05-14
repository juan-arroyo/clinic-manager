# backend/apps/reports/urls.py

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_view, name='index'),
    path('excel/ventas/', views.export_sales_excel, name='export_sales'),
    path('excel/facturas/', views.export_invoices_excel, name='export_invoices'),
    path('excel/fisio/', views.export_fisio_excel, name='export_fisio'),
]