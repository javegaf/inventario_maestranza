from venv import logger
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Producto, ProductoEnKit, KitProducto

@receiver(post_save, sender=Producto)
def actualizar_kits_desde_producto(sender, instance, **kwargs):
    try:
        relaciones = instance.productoenkit_set.select_related('kit').all()
        kits_afectados = {relacion.kit for relacion in relaciones}
        for kit in kits_afectados:
            kit.save()  # Esto activará cualquier lógica de actualización
    except Exception as e:
        logger.error(f"Error actualizando kits: {str(e)}")

@receiver([post_save, post_delete], sender=ProductoEnKit)
def actualizar_kit_desde_componente(sender, instance, **kwargs):
    """
    Actualiza el estado del kit cuando se modifica/elimina un componente
    """
    instance.kit.verificar_estado()