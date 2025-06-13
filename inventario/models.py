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


class LoteProducto(models.Model):
    """Modelo que representa un lote específico de un producto."""
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='lotes')
    numero_lote = models.CharField(max_length=50, unique=True)
    fecha_vencimiento = models.DateField()
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    cantidad_inicial = models.PositiveIntegerField()
    cantidad_actual = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['producto', 'numero_lote']
        ordering = ['fecha_vencimiento']
    
    def __str__(self):
        return f"{self.producto.nombre} - Lote: {self.numero_lote}"
    
    @property
    def esta_vencido(self):
        """Verifica si el lote está vencido."""
        from django.utils import timezone
        return self.fecha_vencimiento < timezone.now().date()
    
    @property
    def dias_hasta_vencimiento(self):
        """Calcula los días hasta el vencimiento."""
        from django.utils import timezone
        delta = self.fecha_vencimiento - timezone.now().date()
        return delta.days
    
    @property
    def porcentaje_usado(self):
        """Calcula el porcentaje usado del lote."""
        if self.cantidad_inicial == 0:
            return 0
        return ((self.cantidad_inicial - self.cantidad_actual) / self.cantidad_inicial) * 100


class HistorialLote(models.Model):
    """Historial de cambios en los lotes."""
    
    TIPO_CAMBIO = [
        ('creacion', 'Creación de lote'),
        ('uso', 'Uso de lote'),
        ('devolucion', 'Devolución al lote'),
        ('vencimiento', 'Marcado como vencido'),
        ('eliminacion', 'Eliminación de lote'),
    ]
    
    lote = models.ForeignKey(LoteProducto, on_delete=models.CASCADE, related_name='historial')
    tipo_cambio = models.CharField(max_length=20, choices=TIPO_CAMBIO)
    cantidad_anterior = models.PositiveIntegerField()
    cantidad_nueva = models.PositiveIntegerField()
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.lote.numero_lote} - {self.get_tipo_cambio_display()}"
    
    class Meta:
        ordering = ['-fecha_cambio']


class MovimientoInventario(models.Model):
    """Modelo que representa un movimiento de inventario (entrada, salida, etc.)."""

    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('devolucion', 'Devolución'),
    ]

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    lote = models.ForeignKey(LoteProducto, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    observaciones = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Save the movement first
        super().save(*args, **kwargs)
        
        # Update batch quantity if batch is specified
        if self.lote:
            self.actualizar_cantidad_lote()
        
        # Update product stock
        self.actualizar_stock_producto()
    
    def actualizar_cantidad_lote(self):
        """Update the batch quantity based on the movement."""
        if not self.lote:
            return
            
        if self.tipo == 'entrada' or self.tipo == 'devolucion':
            self.lote.cantidad_actual += self.cantidad
        elif self.tipo == 'salida':
            self.lote.cantidad_actual -= self.cantidad
        elif self.tipo == 'ajuste':
            # For adjustments, the quantity represents the new total
            cantidad_anterior = self.lote.cantidad_actual
            self.lote.cantidad_actual = self.cantidad
            
        # Ensure quantity doesn't go below 0
        if self.lote.cantidad_actual < 0:
            self.lote.cantidad_actual = 0
            
        self.lote.save()
        
        # Create history record
        HistorialLote.objects.create(
            lote=self.lote,
            tipo_cambio='uso' if self.tipo == 'salida' else 'devolucion' if self.tipo == 'devolucion' else 'uso',
            cantidad_anterior=self.lote.cantidad_actual - (self.cantidad if self.tipo == 'entrada' else -self.cantidad),
            cantidad_nueva=self.lote.cantidad_actual,
            usuario=self.usuario,
            observaciones=f'Movimiento {self.tipo}: {self.cantidad} unidades'
        )
    
    def actualizar_stock_producto(self):
        """Update the product stock based on the movement."""
        if self.tipo == 'entrada' or self.tipo == 'devolucion':
            self.producto.stock_actual += self.cantidad
        elif self.tipo == 'salida':
            self.producto.stock_actual -= self.cantidad
        elif self.tipo == 'ajuste':
            # For adjustments, recalculate total stock from all batches
            total_lotes = LoteProducto.objects.filter(
                producto=self.producto, 
                activo=True
            ).aggregate(total=models.Sum('cantidad_actual'))['total'] or 0
            self.producto.stock_actual = total_lotes
            
        # Ensure stock doesn't go below 0
        if self.producto.stock_actual < 0:
            self.producto.stock_actual = 0
            
        self.producto.save()

    def __str__(self):
        """Retorna una representación del movimiento realizado."""
        lote_info = f" (Lote: {self.lote.numero_lote})" if self.lote else ""
        return f"{self.tipo} - {self.producto}{lote_info} ({self.cantidad})"


class Proveedor(models.Model):
    """Modelo para gestionar proveedores."""

    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100, blank=True)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)
    direccion = models.TextField(blank=True)
    contacto_principal = models.CharField(max_length=100, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    def get_calificacion_promedio(self):
        """Calcula la calificación promedio del proveedor."""
        evaluaciones = self.evaluaciones.all()
        if evaluaciones:
            return sum(e.calificacion for e in evaluaciones) / len(evaluaciones)
        return 0

    def get_total_compras(self):
        """Obtiene el total de compras realizadas a este proveedor."""
        return self.compras.count()


class CompraProveedor(models.Model):
    """Modelo para registrar compras a proveedores."""

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='compras')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateTimeField(auto_now_add=True)
    numero_factura = models.CharField(max_length=50, blank=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    @property
    def total(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"Compra a {self.proveedor.nombre} - {self.producto.nombre}"


class EvaluacionProveedor(models.Model):
    """Modelo para evaluar y calificar proveedores."""

    CALIFICACIONES = [
        (1, 'Muy Malo'),
        (2, 'Malo'),
        (3, 'Regular'),
        (4, 'Bueno'),
        (5, 'Excelente'),
    ]

    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE, related_name='evaluaciones')
    calificacion = models.IntegerField(choices=CALIFICACIONES)
    comentario = models.TextField()
    fecha_evaluacion = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Evaluación de {self.proveedor.nombre} - {self.get_calificacion_display()}"


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

        return f"Alerta: {self.producto.nombre} - {self.fecha_alerta}"


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
