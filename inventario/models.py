from django.db import models
from datetime import datetime
class Producto(models.Model):
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
        return f"{self.nombre} ({self.numero_serie})"
class MovimientoInventario(models.Model):
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
        return f"{self.tipo} - {self.producto} ({self.cantidad})"
class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    contacto = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return str(self.nombre)

class KitProducto(models.Model):
    nombre = models.CharField(max_length=100)
    productos = models.ManyToManyField(Producto, through='ProductoEnKit')

class ProductoEnKit(models.Model):
    kit = models.ForeignKey(KitProducto, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
class HistorialPrecio(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha = models.DateField(auto_now_add=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
class InformeInventario(models.Model):
    nombre = models.CharField(max_length=100)
    fecha_generacion = models.DateTimeField(auto_now_add=True)
    generado_por = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)
    resumen = models.TextField()
    archivo_pdf = models.FileField(upload_to='reportes/', null=True, blank=True)

    def __str__(self):
        if isinstance(self.fecha_generacion, datetime):
            return f"{self.nombre} - {self.fecha_generacion.strftime('%Y-%m-%d')}"
        return self.nombre

class AlertaStock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_alerta = models.DateTimeField(auto_now_add=True)
    mensaje = models.TextField()
    atendido = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta - {self.producto} ({'Resuelta' if self.atendido else 'Pendiente'})"
class AuditoriaInventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    bloqueado = models.BooleanField(default=True)
    motivo = models.TextField(blank=True)
    usuario_auditor = models.ForeignKey('usuarios.Usuario', on_delete=models.SET_NULL, null=True)

    def finalizar(self):
        self.bloqueado = False
        self.save()

    def __str__(self):
        return f"Auditoría: {self.producto} - {'Bloqueado' if self.bloqueado else 'Finalizado'}"
class Proyecto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField(null=True, blank=True)

    def __str__(self):
        return str(self.nombre)
class AsignacionMaterialProyecto(models.Model):
    proyecto = models.ForeignKey(Proyecto, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad_asignada = models.PositiveIntegerField()
    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.producto} → {self.proyecto}"
