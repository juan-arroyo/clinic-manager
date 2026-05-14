# backend/apps/patients/urls.py

from django.urls import path
from . import views

app_name = 'patients'  # namespace para referenciar URLs como 'patients:list' en templates

urlpatterns = [
    path('', views.patient_list, name='list'),
    path('<int:pk>/', views.patient_detail, name='detail'),      # <int:pk> = ID del paciente
    path('nuevo/', views.patient_create, name='create'),
    path('<int:pk>/editar/', views.patient_edit, name='edit'),
]