"""Configuración del panel de administración para el sistema de inventario."""

from django.contrib import admin
from .models import (
    Producto,
    MovimientoInventario,
    Proveedor,
    KitProducto,
    ProductoEnKit,
    HistorialPrecio,
    InformeInventario,
    AlertaStock,
    AuditoriaInventario,
    Proyecto,
    AsignacionMaterialProyecto
)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Producto."""
    list_display = ('nombre', 'numero_serie', 'ubicacion', 'stock_actual', 'stock_minimo')
    list_filter = ('categoria', 'proveedor')
    search_fields = ('nombre', 'numero_serie')


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo MovimientoInventario."""
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'usuario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre',)


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Proveedor."""
    list_display = ('nombre', 'correo', 'telefono')
    search_fields = ('nombre',)


class ProductoEnKitInline(admin.TabularInline):
    """Inline para mostrar productos dentro de un kit en el admin."""
    model = ProductoEnKit
    extra = 1


@admin.register(KitProducto)
class KitProductoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo KitProducto."""
    inlines = [ProductoEnKitInline]
    list_display = ('nombre',)


@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo HistorialPrecio."""
    list_display = ('producto', 'fecha', 'precio_unitario')
    list_filter = ('fecha',)


@admin.register(InformeInventario)
class InformeInventarioAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo InformeInventario."""
    list_display = ('nombre', 'fecha_generacion', 'generado_por')
    list_filter = ('fecha_generacion',)


@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo AlertaStock."""
    list_display = ('producto', 'fecha_alerta', 'atendido')
    list_filter = ('atendido',)


@admin.register(AuditoriaInventario)
class AuditoriaInventarioAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo AuditoriaInventario."""
    list_display = ('producto', 'fecha_inicio', 'bloqueado', 'usuario_auditor')


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo Proyecto."""
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin_estimada')


@admin.register(AsignacionMaterialProyecto)
class AsignacionMaterialProyectoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo AsignacionMaterialProyecto."""
    list_display = ('producto', 'proyecto', 'cantidad_asignada', 'fecha_asignacion')
