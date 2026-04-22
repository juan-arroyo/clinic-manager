# backend/apps/users/urls.py
# URLs del módulo de usuarios.
# Define las rutas relacionadas con autenticación y perfil.

from django.urls import path
from . import views  # importamos las vistas de esta misma app

app_name = 'users'  # namespace — permite usar 'users:login' en las templates

urlpatterns = [
    # Página de login — muestra el formulario y procesa el envío
    path('login/', views.login_view, name='login'),

    # Cerrar sesión
    path('logout/', views.logout_view, name='logout'),

    # Perfil del usuario autenticado
    path('perfil/', views.profile_view, name='profile'),
]