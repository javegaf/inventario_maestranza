# usuarios/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    rol = models.CharField(max_length=30, choices=[
        ('administrador', 'Administrador'),
        ('gestor', 'Gestor de Inventario'),
        ('auditor', 'Auditor'),
        ('logistica', 'Encargado de Logística'),
        ('comprador', 'Comprador'),
        ('produccion', 'Jefe de Producción')
    ])