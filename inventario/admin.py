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
    list_display = ('nombre', 'numero_serie', 'ubicacion', 'stock_actual', 'stock_minimo')
    list_filter = ('categoria', 'proveedor')
    search_fields = ('nombre', 'numero_serie')

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'fecha', 'usuario')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'correo', 'telefono')
    search_fields = ('nombre',)

class ProductoEnKitInline(admin.TabularInline):
    model = ProductoEnKit
    extra = 1

@admin.register(KitProducto)
class KitProductoAdmin(admin.ModelAdmin):
    inlines = [ProductoEnKitInline]
    list_display = ('nombre',)

@admin.register(HistorialPrecio)
class HistorialPrecioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'fecha', 'precio_unitario')
    list_filter = ('fecha',)

@admin.register(InformeInventario)
class InformeInventarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_generacion', 'generado_por')
    list_filter = ('fecha_generacion',)

@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = ('producto', 'fecha_alerta', 'atendido')
    list_filter = ('atendido',)

@admin.register(AuditoriaInventario)
class AuditoriaInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'fecha_inicio', 'bloqueado', 'usuario_auditor')

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_inicio', 'fecha_fin_estimada')

@admin.register(AsignacionMaterialProyecto)
class AsignacionMaterialProyectoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'proyecto', 'cantidad_asignada', 'fecha_asignacion')
