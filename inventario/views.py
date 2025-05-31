"""
Vistas del módulo inventario: productos, 
movimientos, proveedores, kits, alertas, reportes y precios.
"""

from django.shortcuts import render, redirect
from django.db import models
from .models import Producto, MovimientoInventario, Proveedor, KitProducto, HistorialPrecio, AlertaStock
from .forms import ProductoForm, MovimientoInventarioForm, ProveedorForm, KitProductoForm

# Productos

def lista_productos(request):
    """Muestra la lista de productos registrados en el sistema."""
    productos = Producto.objects.all() #Falsos positivos dejar de lado
    return render(request, 'productos/lista_productos.html', {'productos': productos})

def crear_producto(request):
    """Formulario para crear un nuevo producto en el inventario."""
    form = ProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('listar_productos')
    return render(request, 'productos/formulario_producto.html', {'form': form})

# Movimientos

def lista_movimientos(request):
    """Muestra el historial de movimientos de inventario."""
    movimientos = MovimientoInventario.objects.all() #Falsos positivos dejar de lado
    return render(request, 'movimientos/lista_movimientos.html', {'movimientos': movimientos})

def crear_movimiento(request):
    """Formulario para registrar un nuevo movimiento de inventario."""
    form = MovimientoInventarioForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_movimientos')
    return render(request, 'movimientos/formulario_movimiento.html', {'form': form})

# Proveedores

def lista_proveedores(request):
    """Muestra todos los proveedores registrados en el sistema."""
    proveedores = Proveedor.objects.all() #Falsos positivos dejar de lado
    return render(request, 'proveedores/lista_proveedores.html', {'proveedores': proveedores})

def crear_proveedor(request):
    """Formulario para agregar un nuevo proveedor."""
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_proveedores')
    return render(request, 'proveedores/formulario_proveedor.html', {'form': form})

# Alertas de stock

def alertas_stock(request):
    """Muestra productos cuyo stock actual está por debajo del mínimo definido."""
    productos_bajo_stock = Producto.objects.filter(stock_actual__lt=models.F('stock_minimo'))
    

    if request.method == 'POST' and 'alerta_id' in request.POST:
        alerta_id = request.POST.get('alerta_id')
        try:
            alerta = AlertaStock.objects.get(id=alerta_id)
            alerta.atendido = True
            alerta.save()
            return redirect('alertas_stock')
        except AlertaStock.DoesNotExist:
            pass
    
    
    alertas = []
    for producto in productos_bajo_stock:
        alerta, created = AlertaStock.objects.get_or_create(
            producto=producto,
            atendido=False,
            defaults={
                'mensaje': f'El producto {producto.nombre} tiene un stock de {producto.stock_actual} unidades, por debajo del mínimo de {producto.stock_minimo}.'
            }
        )
        alertas.append(alerta)
    
    todas_alertas = AlertaStock.objects.filter(atendido=False)
    
    return render(request, 'alertas/alertas_stock.html', {
        'productos_bajo_stock': productos_bajo_stock,
        'alertas': todas_alertas
    })

# Kits

def lista_kits(request):
    """Muestra la lista de kits de productos disponibles."""
    kits = KitProducto.objects.all() #Falsos positivos dejar de lado
    return render(request, 'kits/lista_kits.html', {'kits': kits})

def crear_kit(request):
    """Formulario para crear un nuevo kit de productos."""
    form = KitProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_kits')
    return render(request, 'kits/formulario_kit.html', {'form': form})

# Reportes

def reportes(request):
    """Vista de reportes disponibles del inventario."""
    return render(request, 'reportes/reportes.html')

# Historial de precios

def historial_precios(request):
    """Muestra el historial de precios por producto."""
    historial = HistorialPrecio.objects.all() #Falsos positivos dejar de lado
    return render(request, 'precios/historial_precios.html', {'historial': historial})
