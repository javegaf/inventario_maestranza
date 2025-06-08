"""
Definiciones de rutas URL para la app de inventario.
Este archivo incluye las rutas asociadas a productos, movimientos de inventario,
proveedores, alertas, kits, reportes e historial de precios.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('productos/', views.lista_productos, name='listar_productos'),
    path('productos/nuevo/', views.crear_producto, name='crear_producto'),

    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/nuevo/', views.crear_movimiento, name='crear_movimiento'),

    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/<int:proveedor_id>/editar/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/<int:proveedor_id>/', views.detalle_proveedor, name='detalle_proveedor'),
    path('proveedores/<int:proveedor_id>/compra/', views.registrar_compra, name='registrar_compra'),
    path('proveedores/<int:proveedor_id>/evaluar/', views.evaluar_proveedor, name='evaluar_proveedor'),

    path('alertas/', views.alertas_stock, name='alertas_stock'),

    path('kits/', views.lista_kits, name='lista_kits'),
    path('kits/nuevo/', views.crear_kit, name='crear_kit'),

    path('reportes/', views.reportes, name='reportes'),
    path('precios/', views.historial_precios, name='historial_precios'),

    path('productos/<int:producto_id>/toggle-block/', views.toggle_block_product, name='toggle_block_product'),

    path('productos/historial-bloqueos/', views.historial_bloqueos, name='historial_bloqueos'),
]