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
    
    @property
    def diferencia(self):
        """Calcula la diferencia entre cantidad nueva y anterior."""
        return self.cantidad_nueva - self.cantidad_anterior
    
    @property
    def tipo_diferencia(self):
        """Retorna el tipo de diferencia: positiva, negativa o neutra."""
        diff = self.diferencia
        if diff > 0:
            return 'positiva'
        elif diff < 0:
            return 'negativa'
        else:
            return 'neutra'
    
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

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        # Save the purchase first
        super().save(*args, **kwargs)
        
        # Create price history record automatically only for new purchases
        if is_new:
            HistorialPrecio.objects.create(
                producto=self.producto,
                precio_unitario=self.precio_unitario,
                proveedor=self.proveedor,
                compra=self,
                usuario=self.usuario,
                observaciones=f'Precio registrado por compra - Factura: {self.numero_factura or "Sin número"}'
            )

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

    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='precios')
    fecha = models.DateTimeField(auto_now_add=True)  # Changed to DateTimeField for better precision
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True, blank=True)  # New field
    compra = models.ForeignKey(CompraProveedor, on_delete=models.SET_NULL, null=True, blank=True)  # New field
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)  # New field
    observaciones = models.TextField(blank=True)  # New field
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Historial de Precio'
        verbose_name_plural = 'Historial de Precios'
    
    def __str__(self):
        return f"{self.producto.nombre} - ${self.precio_unitario} ({self.fecha.strftime('%d/%m/%Y')})"
    
    @property
    def precio_anterior(self):
        """Get the previous price for this product."""
        precio_anterior = HistorialPrecio.objects.filter(
            producto=self.producto,
            fecha__lt=self.fecha
        ).first()
        return precio_anterior.precio_unitario if precio_anterior else None
    
    @property
    def variacion_precio(self):
        """Calculate price variation from previous price."""
        anterior = self.precio_anterior
        if anterior:
            return self.precio_unitario - anterior
        return None
    
    @property
    def porcentaje_variacion(self):
        """Calculate percentage variation from previous price."""
        anterior = self.precio_anterior
        if anterior and anterior > 0:
            return ((self.precio_unitario - anterior) / anterior) * 100
        return None


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
    """Modelo para representar proyectos que utilizan materiales del inventario."""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField(blank=True, null=True)
    fecha_fin_real = models.DateField(blank=True, null=True)
    responsable = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                   blank=True, null=True, related_name='proyectos_responsable')
    estado = models.CharField(max_length=20, choices=[
        ('planificacion', 'En Planificación'),
        ('ejecucion', 'En Ejecución'),
        ('completado', 'Completado'),
        ('suspendido', 'Suspendido'),
        ('cancelado', 'Cancelado')
    ], default='planificacion')
    notas = models.TextField(blank=True, null=True)
    creado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, 
                                  blank=True, null=True, related_name='proyectos_creados')
    fecha_creacion = models.DateTimeField(blank=True , null=True)
    fecha_actualizacion = models.DateTimeField(blank=True , null=True)
    
    class Meta:
        ordering = ['-fecha_inicio']
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'
    
    def __str__(self):
        return self.nombre
    
    @property
    def total_materiales(self):
        """Devuelve el total de materiales asignados al proyecto."""
        return self.materiales.count()
    
    @property
    def costo_total_estimado(self):
        """Calcula el costo total estimado del proyecto basado en los materiales asignados."""
        return sum(material.costo_total for material in self.materiales.all())
    
    @property
    def dias_restantes(self):
        """Calcula los días restantes hasta la fecha de finalización estimada."""
        if not self.fecha_fin_estimada:
            return None
        if self.estado == 'completado':
            return 0
        
        dias = (self.fecha_fin_estimada - timezone.now().date()).days
        return max(0, dias)
    
    @property
    def progreso(self):
        """Calcula el progreso aproximado del proyecto."""
        if self.estado == 'completado':
            return 100
        if self.estado == 'planificacion':
            return 0
            
        # Si está en ejecución, calcular basado en tiempo transcurrido
        if self.fecha_fin_estimada and self.fecha_inicio:
            duracion_total = (self.fecha_fin_estimada - self.fecha_inicio).days
            if duracion_total <= 0:
                return 50  # Valor por defecto si las fechas no son coherentes
                
            dias_transcurridos = (timezone.now().date() - self.fecha_inicio).days
            progreso = min(99, int((dias_transcurridos / duracion_total) * 100))
            return max(1, progreso)  # Al menos 1% si ya comenzó
            
        return 50  # Valor por defecto


class MaterialProyecto(models.Model):
    """Materiales asignados a un proyecto específico."""
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE, related_name='materiales')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='proyectos')
    cantidad_asignada = models.PositiveIntegerField()
    cantidad_utilizada = models.PositiveIntegerField(default=0)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    lote = models.ForeignKey(LoteProducto, on_delete=models.SET_NULL, blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Material de Proyecto'
        verbose_name_plural = 'Materiales de Proyectos'
        unique_together = ['proyecto', 'producto', 'lote']
    
    def __str__(self):
        return f"{self.producto.nombre} - {self.proyecto.nombre}"
    
    @property
    def costo_total(self):
        """Calcula el costo total de este material en el proyecto."""
        # Obtener el precio más reciente del producto
        ultimo_precio = HistorialPrecio.objects.filter(producto=self.producto).order_by('-fecha').first()
        precio_unitario = ultimo_precio.precio_unitario if ultimo_precio else 0
        return precio_unitario * self.cantidad_asignada
    
    @property
    def cantidad_disponible(self):
        """Calcula la cantidad que aún queda disponible para usar."""
        return self.cantidad_asignada - self.cantidad_utilizada
    
    @property
    def porcentaje_utilizado(self):
        """Calcula el porcentaje de material utilizado."""
        if self.cantidad_asignada == 0:
            return 0
        return (self.cantidad_utilizada / self.cantidad_asignada) * 100

class ConfiguracionSistema(models.Model):
    """Configuración global del sistema de control de inventario.

    Este modelo permite almacenar y modificar parámetros clave que controlan
    el comportamiento del sistema sin necesidad de cambiar el código fuente.
    """

    CLAVES_CHOICES = [
        ('umbral_stock_critico', 'Umbral de Stock Crítico'),
        ('umbral_stock_bajo', 'Umbral de Stock Bajo'),
        ('modo_mantenimiento', 'Modo Mantenimiento'),
        ('auto_generar_orden_compra', 'Auto-generar Orden de Compra'),
        ('proveedor_default', 'Proveedor Default'),
        ('registro_de_auditorias', 'Registro de Auditorías'),
        ('mostrar_mensaje_bienvenida', 'Mostrar Mensaje de Bienvenida'),
        ('formato_fecha_preferido', 'Formato de Fecha Preferido'),
    ]

    clave = models.CharField(
        max_length=100,
        choices=CLAVES_CHOICES,
        unique=True,
        help_text="Nombre interno del parámetro de configuración."
    )
    valor = models.CharField(
        max_length=255,
        help_text="Valor asignado al parámetro (texto o número según contexto)."
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción explicativa del propósito de este parámetro."
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
        ordering = ['clave']

    def __str__(self):
        """Retorna una representación legible del parámetro configurado."""
        return f"{self.get_clave_display()}: {self.valor}"

class AuditoriaInformeInventario(models.Model):
    """Auditoría de generación de informes de inventario (PDF o Excel)."""

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    fecha = models.DateTimeField(auto_now_add=True)
    filtros_aplicados = models.TextField(help_text="Filtros usados al generar el informe (formato JSON o texto plano).")
    tipo_exportacion = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF'), ('excel', 'Excel')],
        help_text="Formato en que se exportó el informe."
    )
    total_registros = models.PositiveIntegerField(help_text="Cantidad de productos exportados.")

    def __str__(self):
        return f"Informe {self.tipo_exportacion.upper()} - {self.usuario} - {self.fecha.strftime('%Y-%m-%d %H:%M')}"
