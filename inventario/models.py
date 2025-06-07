"""Modelos del sistema de control de inventario."""

from datetime import datetime
from django.db import models
from django.utils import timezone
from django.conf import settings

class Producto(models.Model):
    """Modelo que representa un producto individual del inventario."""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    numero_serie = models.CharField(max_length=50, unique=True)
    ubicacion = models.CharField(max_length=100)
    categoria = models.CharField(max_length=100)
    proveedor = models.ForeignKey('Proveedor', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    stock_actual = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Retorna una representación legible del producto."""
        return f"{self.nombre} ({self.numero_serie})"

    @property
    def is_blocked(self):
        """Check if the product is currently blocked."""
        return AuditoriaInventario.objects.filter(
            producto=self, 
            bloqueado=True
        ).exists()
    
    def get_active_block(self):
        """Return the active block for this product, if any."""
        return AuditoriaInventario.objects.filter(
            producto=self, 
            bloqueado=True
        ).first()


class MovimientoInventario(models.Model):
    """Modelo que representa un movimiento de inventario (entrada, salida, etc.)."""

    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('devolucion', 'Devolución'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        """Retorna una representación del movimiento realizado."""
        return f"{self.tipo} - {self.producto} ({self.cantidad})"


class Proveedor(models.Model):
    """Modelo que representa un proveedor externo."""

    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)

    def __str__(self):
        """Retorna el nombre del proveedor."""
        return str(self.nombre)


class KitProducto(models.Model):
    """Modelo que representa un kit compuesto por varios productos."""

    nombre = models.CharField(max_length=100)
    productos = models.ManyToManyField(Producto, through='ProductoEnKit')


class ProductoEnKit(models.Model):
    """Modelo intermedio que vincula productos a un kit específico."""

    kit = models.ForeignKey(KitProducto, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()


class HistorialPrecio(models.Model):
    """Registro histórico de precios unitarios por producto."""

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)


class InformeInventario(models.Model):
    """Modelo para informes generados del inventario."""

    nombre = models.CharField(max_length=100)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    generado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    resumen = models.TextField()
    archivo_pdf = models.FileField(upload_to='reportes/', null=True, blank=True)

    def __str__(self):
        """Retorna el nombre y fecha del informe."""
        if isinstance(self.fecha_generacion, datetime):
            return f"{self.nombre} - {self.fecha_generacion.strftime('%Y-%m-%d')}"
        return self.nombre


class AlertaStock(models.Model):
    """Alerta generada cuando un producto está bajo el stock mínimo."""

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    mensaje = models.TextField()
    atendido = models.BooleanField(default=False)

    def __str__(self):
        """Muestra si la alerta fue atendida o sigue pendiente."""
        return f"Alerta - {self.producto} ({'Resuelta' if self.atendido else 'Pendiente'})"


class AuditoriaInventario(models.Model):
    """Bloqueo temporal de producto mientras se realiza una auditoría."""

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)  # This field is missing in the database
    bloqueado = models.BooleanField(default=False)
    motivo = models.TextField(blank=True)
    usuario_auditor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    def finalizar(self):
        """Mark the block as finished by setting an end date."""
        self.fecha_fin = timezone.now()
        self.bloqueado = False
        self.save()
        
    def __str__(self):
        status = "Bloqueado" if self.bloqueado else "Desbloqueado"
        return f"{self.producto.nombre} - {status} - {self.fecha_inicio}"


class Proyecto(models.Model):
    """Proyecto al que se le asignan productos del inventario."""

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField(null=True, blank=True)

    def __str__(self):
        """Retorna el nombre del proyecto."""
        return str(self.nombre)


class AsignacionMaterialProyecto(models.Model):
    """Asociación de productos asignados a un proyecto específico."""

    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_asignada = models.PositiveIntegerField()
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Retorna una cadena que relaciona producto con proyecto."""
        return f"{self.producto} → {self.proyecto}"
