"""Definiciones de rutas URL para la app de usuarios."""

from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views
from .views import CustomLoginView

# pylint: disable=invalid-name
# Para evitar problemas con pylint
app_name = "usuarios"

urlpatterns = [
    path('', views.home, name='home'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='usuarios:home'), name='logout'),
]
