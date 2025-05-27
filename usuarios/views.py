from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def perfil_usuario(request):
    return render(request, 'usuarios/perfil.html')

def home(request):
    return render(request, 'home.html')
