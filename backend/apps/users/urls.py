# backend/apps/users/urls.py

from django.urls import path
from . import views

app_name = 'users'  # namespace para referenciar URLs como 'users:login' en templates

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.profile_view, name='profile'),
    path('', views.dashboard_view, name='dashboard'),
]