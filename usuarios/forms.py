"""Formularios personalizados de usuarios para el sistema de inventario."""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

# Roles permitidos en registro libre
ROLES_POR_DEFECTO = [
    ('logistica', 'Encargado de Logística'),
    ('comprador', 'Comprador'),
    ('produccion', 'Jefe de Producción'),
]

class RegistroForm(UserCreationForm):
    """Formulario de registro público de nuevos usuarios con roles limitados."""

    email = forms.EmailField(required=True)

    class Meta:
        """Configuración de campos para el formulario de registro."""
        model = Usuario
        fields = ["username", "email", "rol", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        """Inicializa el formulario limitando los roles permitidos."""
        super().__init__(*args, **kwargs)
        self.fields['rol'].choices = ROLES_POR_DEFECTO

    def clean_rol(self):
        """Valida que el rol esté dentro de los roles permitidos para registro libre."""
        rol = self.cleaned_data.get('rol')
        if rol not in dict(ROLES_POR_DEFECTO):
            raise forms.ValidationError("No puedes elegir ese rol.")
        return rol

class UsuarioAdminCreationForm(UserCreationForm):
    """Formulario de creación de usuario completo (para administradores)."""

    class Meta:
        """Configuración de campos para el formulario de creación de usuario."""
        model = Usuario
        fields = ['username', 'email', 'rol', 'password1', 'password2']

    def clean_rol(self):
        """Valida que el rol sea válido dentro de las opciones definidas en el modelo."""
        rol = self.cleaned_data.get('rol')
        if rol not in dict(Usuario.ROL_CHOICES):
            raise forms.ValidationError("Rol inválido.")
        return rol

class UsuarioAdminChangeForm(UserChangeForm):
    """Formulario de modificación de usuario completo (para administradores)."""

    class Meta:
        """Configuración de campos para el formulario de modificación de usuario."""
        model = Usuario
        fields = ['username', 'email', 'rol']
