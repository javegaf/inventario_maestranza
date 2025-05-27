from django.urls import path
from . import views

urlpatterns = [
    path('perfil/', views.perfil_usuario, name='perfil'),
    path('', views.home, name='home'),  # Ruta al home
]
