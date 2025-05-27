"""Definiciones de rutas URL para la app de usuarios."""

from django.urls import path
from . import views

# pylint: disable=invalid-name
# Para evitar problemas con pylint
app_name = "usuarios"

urlpatterns = [
    path('', views.home, name='home'),
    path('perfil/', views.perfil_usuario, name='perfil'),
]
