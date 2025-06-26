"""Definición de rutas URL para la app de inventario."""

from django.urls import path
from . import views

app_name = "inventario"  # pylint: disable=invalid-name

urlpatterns = [
    path('productos/', views.lista_productos, name='listar_productos'),
    path('productos/crear/', views.crear_producto, name='crear_producto'),
    path('productos/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('productos/eliminar/<int:producto_id>/',
         views.eliminar_producto, name='eliminar_producto'),
    path('productos/<int:producto_id>/toggle-block/',
         views.toggle_block_product, name='toggle_block_product'),
    path('productos/historial-bloqueos/', views.historial_bloqueos, name='historial_bloqueos'),

    path('movimientos/', views.lista_movimientos, name='lista_movimientos'),
    path('movimientos/nuevo/', views.crear_movimiento, name='crear_movimiento'),

    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/crear/', views.crear_proveedor, name='crear_proveedor'),
    path('proveedores/<int:proveedor_id>/editar/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/<int:proveedor_id>/', views.detalle_proveedor, name='detalle_proveedor'),
    path('proveedores/<int:proveedor_id>/compra/', views.registrar_compra, name='registrar_compra'),
    path('proveedores/<int:proveedor_id>/evaluar/',
         views.evaluar_proveedor, name='evaluar_proveedor'),

    path('alertas/', views.alertas_stock, name='alertas_stock'),

    path('kits/', views.lista_kits, name='lista_kits'),
    path('kits/nuevo/', views.crear_kit, name='crear_kit'),
    path('kits/<int:kit_id>/editar/', views.editar_kit, name='editar_kit'),
    path('kits/<int:pk>/eliminar/', views.eliminar_kit, name='eliminar_kit'),

    path('reportes/', views.reportes, name='reportes'),
    path('reportes/exportar/csv/', views.exportar_csv, name='exportar_csv'),
    path('reportes/exportar/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('reportes/informe-personalizado/', views.informe_inventario, name='informe_inventario'),


    path('precios/', views.historial_precios, name='historial_precios'),
    path('precios/producto/<int:producto_id>/',
         views.historial_precios_producto, name='historial_precios_producto'),
    path('precios/proveedor/<int:proveedor_id>/',
         views.historial_precios_proveedor, name='historial_precios_proveedor'),
    path('precios/comparar/',
         views.comparar_precios_proveedores, name='comparar_precios_proveedores'),
    path('precios/registrar/', views.registrar_precio_manual, name='registrar_precio_manual'),
    path('precios/exportar/csv/', views.exportar_precios_csv, name='exportar_precios_csv'),
    path('precios/exportar/pdf/', views.reporte_precios_pdf, name='reporte_precios_pdf'),

    path('dashboard/', views.dashboard_inventario, name='dashboard'),

    path('productos/<int:producto_id>/lotes/',
         views.detalle_producto_lotes, name='detalle_producto_lotes'),
    path('productos/<int:producto_id>/lotes/crear/', views.crear_lote, name='crear_lote'),
    path('lotes/<int:lote_id>/editar/', views.editar_lote, name='editar_lote'),
    path('lotes/historial/', views.historial_lotes, name='historial_lotes'),
    path('lotes/<int:lote_id>/historial/', views.historial_lotes, name='historial_lote_individual'),

    path('api/productos/<int:producto_id>/lotes/',
         views.api_lotes_producto, name='api_lotes_producto'),

    # Proyectos
    path('proyectos/', views.listar_proyectos, name='listar_proyectos'),
    path('proyectos/crear/', views.crear_proyecto, name='crear_proyecto'),
    path('proyectos/<int:proyecto_id>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('proyectos/<int:proyecto_id>/editar/', views.editar_proyecto, name='editar_proyecto'),
    path('proyectos/<int:proyecto_id>/asignar-material/',
         views.asignar_material, name='asignar_material'),
    path('proyectos/materiales/<int:material_id>/uso/',
         views.actualizar_uso_material, name='actualizar_uso_material'),
    path('proyectos/materiales/<int:material_id>/eliminar/',
         views.eliminar_material, name='eliminar_material'),
    path('api/productos/<int:producto_id>/info/',
         views.api_producto_info, name='api_producto_info'),

    path('configuracion/', views.configuracion_sistema, name='configuracion_sistema'),
]
