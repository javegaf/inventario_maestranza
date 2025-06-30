"""
Definiciones de rutas principales del proyecto Django.
Este archivo conecta las rutas globales del proyecto con las apps internas:
- 'usuarios': manejo de autenticación, perfil y página de inicio.
- 'inventario': gestión de productos, movimientos, proveedores, reportes, etc.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls', namespace='usuarios')),
    path('inventario/', include('inventario.urls', namespace='inventario')),
    path('select2/', include('django_select2.urls')),
]
