# backend/apps/bonuses/urls.py
# URLs del módulo de bonos.

from django.urls import path
from . import views

app_name = 'bonuses'

urlpatterns = [
    # Listado de bonos
    path('', views.bonus_list, name='list'),

    # Detalle de un bono
    path('<int:pk>/', views.bonus_detail, name='detail'),

    # Crear nuevo bono
    path('nuevo/', views.bonus_create, name='create'),
]