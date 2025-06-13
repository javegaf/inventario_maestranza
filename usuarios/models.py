"""Modelo de usuario personalizado para el sistema de inventario."""

from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    """
    Extiende el modelo de usuario de Django para incluir el campo de rol.
    """

    ROL_CHOICES = [
        ('administrador', 'Administrador'),
        ('gestor', 'Gestor de Inventario'),
        ('auditor', 'Auditor'),
        ('logistica', 'Encargado de Logística'),
        ('comprador', 'Comprador'),
        ('produccion', 'Jefe de Producción'),
    ]

    rol = models.CharField(max_length=30, choices=ROL_CHOICES)
