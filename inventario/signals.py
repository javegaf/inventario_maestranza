from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AlertaStock, OrdenCompra, OrdenCompraLog
from .utils import generar_ordenes_sugeridas  # o desde donde esté la función
from .middlewares import get_current_user

@receiver(post_save, sender=AlertaStock)
def crear_orden_sugerida_si_alerta_nueva(sender, instance, created, **kwargs):
    if created and not instance.atendido:
        generar_ordenes_sugeridas()

@receiver(post_save, sender=OrdenCompra)
def registrar_cambio_estado_orden(sender, instance, created, **kwargs):
    usuario = get_current_user()
    if created:
        # Si la orden es nueva, registramos creación
        OrdenCompraLog.objects.create(
            orden=instance,
            estado=instance.estado,
            descripcion='Orden creada automáticamente',
            usuario=usuario
        )
    else:
        # Orden ya existente: buscamos el último log
        ultimo_log = OrdenCompraLog.objects.filter(orden=instance).order_by('-fecha').first()
        if not ultimo_log or ultimo_log.estado != instance.estado:
            # Solo registramos si el estado cambió
            OrdenCompraLog.objects.create(
                orden=instance,
                estado=instance.estado,
                descripcion=f"Estado cambiado a '{instance.get_estado_display()}'",
                usuario=usuario
            )