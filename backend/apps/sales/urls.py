# backend/apps/sales/urls.py
# URLs del módulo de ventas.

from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Listado de ventas
    path('', views.sale_list, name='list'),

    # Detalle de una venta
    path('<int:pk>/', views.sale_detail, name='detail'),

    # Crear nueva venta
    path('nueva/', views.sale_create, name='create'),

    # Editar venta existente
    path('<int:pk>/editar/', views.sale_edit, name='edit'),


    # Endpoint HTMX — devuelve los bonos activos de un paciente
    # Se llama automáticamente cuando el usuario cambia el paciente en el formulario
    path('bonos-paciente/', views.get_patient_bonuses, name='patient_bonuses'),

    
]