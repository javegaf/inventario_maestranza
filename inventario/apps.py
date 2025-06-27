"""Configuración de la aplicación Inventario."""
from django.apps import AppConfig


class InventarioConfig(AppConfig):
    """Configuration for the Inventario app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario'
    
    def ready(self):
        import inventario.signals
