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
    path('proveedores/nuevo/', views.crear_proveedor, name='crear_proveedor'),

    path('alertas/', views.alertas_stock, name='alertas_stock'),

    path('kits/', views.lista_kits, name='lista_kits'),
    path('kits/nuevo/', views.crear_kit, name='crear_kit'),

    path('reportes/', views.reportes, name='reportes'),
    path('precios/', views.historial_precios, name='historial_precios'),
]