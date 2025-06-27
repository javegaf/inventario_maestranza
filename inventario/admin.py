"""Configuración del panel de administración para el sistema de inventario."""

from django.contrib import admin
from .models import (
    Producto, MovimientoInventario,
    Proveedor, KitProducto,
    ProductoEnKit, HistorialPrecio, InformeInventario, AlertaStock,
    AuditoriaInventario, Proyecto, MaterialProyecto, ConfiguracionSistema,
    OrdenCompra, ItemOrdenCompra, LoteProducto
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


@admin.register(MaterialProyecto)  # Changed from AsignacionMaterialProyecto
class MaterialProyectoAdmin(admin.ModelAdmin):
    """Configuración del admin para el modelo AsignacionMaterialProyecto."""
    list_display = ('producto', 'proyecto', 'cantidad_asignada', 'fecha_asignacion')

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """Admin para gestionar configuraciones generales del sistema."""
    list_display = ['clave', 'valor', 'descripcion', 'fecha_actualizacion']
    list_editable = ['valor']
    search_fields = ['clave', 'descripcion']
    list_filter = ['clave']
    ordering = ['clave']

class ItemOrdenCompraInline(admin.TabularInline):
    model = ItemOrdenCompra
    extra = 0
    readonly_fields = ('producto', 'cantidad')
    can_delete = False

@admin.register(OrdenCompra)
class OrdenCompraAdmin(admin.ModelAdmin):
    list_display = ('id', 'proveedor', 'estado', 'fecha_creacion', 'observaciones_corta')
    list_filter = ('estado', 'proveedor')
    search_fields = ('proveedor__nombre',)
    inlines = [ItemOrdenCompraInline]
    readonly_fields = ('fecha_creacion',)

    def observaciones_corta(self, obj):
        return (obj.observaciones[:50] + '...') if obj.observaciones and len(obj.observaciones) > 50 else obj.observaciones
    observaciones_corta.short_description = 'Observaciones'


@admin.register(LoteProducto)
class LoteProductoAdmin(admin.ModelAdmin):
    list_display = (
        'numero_lote',
        'producto',
        'fecha_vencimiento',
        'cantidad_inicial',
        'cantidad_actual',
        'observaciones',
    )
    list_filter = ('producto', 'fecha_vencimiento')
    search_fields = ('numero_lote', 'producto__nombre', 'observaciones')
    ordering = ('-fecha_vencimiento',)