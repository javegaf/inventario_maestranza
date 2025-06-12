"""Definición de rutas URL para la app de usuarios."""

from django.urls import path
from . import views
from .views import CustomLoginView, registro_view, custom_logout_view

APP_NAME = "usuarios"  # Pylint friendly

urlpatterns = [
    path('', views.home, name='home'),
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout_view, name='logout'),
    path('registro/', registro_view, name='registro'),

    # CRUD usuarios (solo admin)
    path('admin/usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('admin/usuarios/crear/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('admin/usuarios/editar/<int:pk>/',
         views.editar_usuario_admin, name='editar_usuario_admin'),
    path('admin/usuarios/eliminar/<int:pk>/',
         views.eliminar_usuario_admin, name='eliminar_usuario_admin'),
]
