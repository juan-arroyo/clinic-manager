# backend/apps/patients/urls.py
# URLs del módulo de pacientes.

from django.urls import path
from . import views

app_name = 'patients'  # namespace — permite usar 'patients:list' en las templates

urlpatterns = [
    # Listado de pacientes con buscador
    path('', views.patient_list, name='list'),

    # Detalle de un paciente — <int:pk> es el ID del paciente en la URL
    path('<int:pk>/', views.patient_detail, name='detail'),

    # Crear nuevo paciente
    path('nuevo/', views.patient_create, name='create'),

    # Editar paciente existente
    path('<int:pk>/editar/', views.patient_edit, name='edit'),
]