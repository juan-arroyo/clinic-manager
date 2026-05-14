# backend/apps/bonuses/urls.py

from django.urls import path
from . import views

app_name = 'bonuses'

urlpatterns = [
    path('', views.bonus_list, name='list'),
    path('<int:pk>/', views.bonus_detail, name='detail'),
    path('nuevo/', views.bonus_create, name='create'),
    # Endpoint HTMX — responde búsquedas de paciente en tiempo real
    path('buscar-paciente/', views.search_patients, name='search_patients'),
]