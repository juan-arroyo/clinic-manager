# backend/apps/sales/urls.py

from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('', views.sale_list, name='list'),
    path('<int:pk>/', views.sale_detail, name='detail'),
    path('nueva/', views.sale_create, name='create'),
    path('<int:pk>/editar/', views.sale_edit, name='edit'),

    # Endpoints HTMX — responden fragmentos HTML sin recargar la página
    path('bonos-paciente/', views.get_patient_bonuses, name='patient_bonuses'),       # bonos activos al cambiar paciente
    path('buscar-paciente/', views.search_patients_sales, name='search_patients'),    # búsqueda en tiempo real

    # Ciclo de vida de la factura
    path('<int:pk>/factura/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/factura/crear/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/factura/editar/', views.invoice_edit, name='invoice_edit'),
    path('<int:pk>/factura/pdf/', views.generate_invoice_pdf, name='invoice_pdf'),
    path('<int:pk>/factura/enviar/', views.invoice_send, name='invoice_send'),
]