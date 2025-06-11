from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

# Roles permitidos en registro libre
ROLES_POR_DEFECTO = [
    ('logistica', 'Encargado de Logística'),
    ('comprador', 'Comprador'),
    ('produccion', 'Jefe de Producción'),
]

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Usuario
        fields = ["username", "email", "rol", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].choices = ROLES_POR_DEFECTO

    def clean_rol(self):
        rol = self.cleaned_data.get('rol')
        if rol not in dict(ROLES_POR_DEFECTO):
            raise forms.ValidationError("No puedes elegir ese rol.")
        return rol
