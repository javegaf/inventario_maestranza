"""Vistas del módulo de usuarios para el sistema de inventario."""

from django.contrib import messages as django_messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import RegistroForm, UsuarioAdminCreationForm, UsuarioAdminChangeForm
from .models import Usuario

@login_required
def home(request):
    """Vista principal del sistema (home)."""
    return render(request, 'home.html')

@login_required
def perfil_usuario(request):
    """Vista de perfil del usuario autenticado."""
    return render(request, 'usuarios/perfil.html')

class CustomLoginView(LoginView):
    """Vista personalizada de login para usuarios."""

    template_name = 'registro_login/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Mensaje de bienvenida al iniciar sesión."""
        django_messages.success(self.request, f"Bienvenido, {form.get_user().username}")
        return super().form_valid(form)

    def get_success_url(self):
        """Redirecciona según el rol del usuario."""
        user = self.request.user
        if user.rol == 'administrador':
            return reverse_lazy('usuarios:perfil')
        elif user.rol in ['logistica', 'comprador', 'produccion']:
            return reverse_lazy('usuarios:home')
        return reverse_lazy('usuarios:home')

def registro_view(request):
    """Vista de registro público de usuarios (roles limitados)."""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            django_messages.success(request, "Registro exitoso. Ahora puedes iniciar sesión.")
            return redirect('usuarios:login')
    else:
        form = RegistroForm()
    return render(request, 'registro_login/registro.html', {'form': form})

def custom_logout_view(request):
    """Cierra la sesión del usuario."""
    logout(request)
    django_messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('usuarios:login')

# ======== CRUD ADMIN USUARIOS ==========

def es_administrador(user):
    """Verifica si el usuario es administrador."""
    return user.is_authenticated and user.rol == 'administrador'

@user_passes_test(es_administrador)
def lista_usuarios(request):
    """Muestra la lista de usuarios del sistema."""
    usuarios = Usuario.objects.all()
    return render(request, 'usuarios/lista_usuarios.html', {'usuarios': usuarios})

@user_passes_test(es_administrador)
def crear_usuario_admin(request):
    """Permite al administrador crear un nuevo usuario."""
    if request.method == 'POST':
        form = UsuarioAdminCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('usuarios:lista_usuarios')
    else:
        form = UsuarioAdminCreationForm()
    return render(request, 'usuarios/form_usuario_admin.html', {'form': form})

@user_passes_test(es_administrador)
def editar_usuario_admin(request, pk):
    """Permite al administrador editar un usuario existente."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioAdminChangeForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            return redirect('usuarios:lista_usuarios')
    else:
        form = UsuarioAdminChangeForm(instance=usuario)
    return render(request, 'usuarios/form_usuario_admin.html', {'form': form})

@user_passes_test(es_administrador)
def eliminar_usuario_admin(request, pk):
    """Permite al administrador eliminar un usuario."""
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        return redirect('usuarios:lista_usuarios')
    return render(request, 'usuarios/confirmar_eliminar_usuario.html', {'usuario': usuario})
