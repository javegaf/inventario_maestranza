"""Vistas del módulo de usuarios: home y perfil."""

from django.contrib import messages as django_messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from .forms import RegistroForm

@login_required
def perfil_usuario(request):
    """Muestra la vista del perfil del usuario autenticado."""
    return render(request, 'usuarios/perfil.html')

def home(request):
    """Vista principal de inicio del sistema (home)."""
    return render(request, 'home.html')
class CustomLoginView(LoginView):
    template_name = 'registro_login/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        django_messages.success(self.request, f"Bienvenido, {form.get_user().username}")
        return super().form_valid(form)

    def get_success_url(self):
        user = self.request.user
        # Redirección por rol
        if user.rol == 'administrador':
            return reverse_lazy('usuarios:perfil')
        elif user.rol == 'logistica':
            return reverse_lazy('usuarios:home')
        elif user.rol == 'comprador':
            return reverse_lazy('usuarios:home')
        # Default
        return reverse_lazy('usuarios:home')

def registro_view(request):
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
    logout(request)
    django_messages.info(request, "Has cerrado sesión correctamente.")
    return redirect('usuarios:login')  # O 'usuarios:home', lo que tú prefieras
