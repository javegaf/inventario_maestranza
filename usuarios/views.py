"""Vistas del módulo de usuarios: home y perfil."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def perfil_usuario(request):
    """Muestra la vista del perfil del usuario autenticado."""
    return render(request, 'usuarios/perfil.html')

def home(request):
    """Vista principal de inicio del sistema (home)."""
    return render(request, 'home.html')
