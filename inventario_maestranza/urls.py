from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),  # Ruta raíz y home
    path('', include('inventario.urls')),
    path('usuarios/', include('usuarios.urls')),  # Para vista de perfil, login
]
