"""Configuración del panel de administración para el modelo de usuario personalizado."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Configuración del admin para el modelo Usuario personalizado."""

    model = Usuario
    list_display = ('username', 'email', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('Rol y permisos extendidos', {'fields': ('rol',)}),
    )
