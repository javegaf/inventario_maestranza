"""
Vistas del módulo inventario: productos, 
movimientos, proveedores, kits, alertas, reportes y precios.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from .models import AlertaStock, Producto, MovimientoInventario, Proveedor, KitProducto, HistorialPrecio
from .forms import ProductoForm, MovimientoInventarioForm, ProveedorForm, KitProductoForm, ProductoEditableForm
from django.db.models import F, Count

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
    #Falsos positivos dejar de lado
    return render(request, 'alertas/alertas_stock.html',
                  {'productos_bajo_stock': productos_bajo_stock})

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

@login_required
def dashboard_inventario(request):
    total_productos = Producto.objects.count()
    productos_sin_stock = Producto.objects.filter(stock_actual=0).count()
    productos_bajo_minimo = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).count()
    movimientos = (
        MovimientoInventario.objects.values('tipo')
        .annotate(total=Count('id'))
        .order_by('tipo')
    )

    tipos = [m['tipo'].capitalize() for m in movimientos]
    cantidades = [m['total'] for m in movimientos]
    colores_contexto = {
        'Entrada': 'rgba(75, 192, 192, 0.6)',     # Verde azulado
        'Salida': 'rgba(255, 99, 132, 0.6)',      # Rojo
        'Ajuste': 'rgba(255, 206, 86, 0.6)',      # Amarillo
        'Devolucion': 'rgba(54, 162, 235, 0.6)',  # Azul
    }

    colores_barras = [colores_contexto.get(tipo.capitalize(), 'rgba(153, 102, 255, 0.6)') for tipo in tipos]

    alertas_stock = AlertaStock.objects.filter(atendido=False).select_related('producto').order_by('-fecha_alerta')

    proveedores = (
        Producto.objects.values('proveedor__nombre')
        .annotate(total=Count('id'))
        .order_by('-total')
    )

    nombres_proveedores = [p['proveedor__nombre'] or 'Sin proveedor' for p in proveedores]
    cantidades_proveedor = [p['total'] for p in proveedores]
    context = {
        'total_productos': total_productos,
        'productos_sin_stock': productos_sin_stock,
        'productos_bajo_minimo': productos_bajo_minimo,
        'tipos_movimiento': tipos,
        'cantidades_movimiento': cantidades,
        'colores_barras': colores_barras,
        'alertas_stock': alertas_stock,
        'nombres_proveedores': nombres_proveedores,
        'cantidades_proveedor': cantidades_proveedor,
    }
    return render(request, 'inventario/dashboard.html', context)

def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id)
    fecha_actual = producto.fecha_vencimiento 
    if request.method == 'POST':
        form = ProductoEditableForm(request.POST, instance=producto)
        if form.is_valid():
            producto_editado = form.save(commit=False)
            
            if not form.cleaned_data.get('fecha_vencimiento'):
                producto_editado.fecha_vencimiento = fecha_actual
            
            producto_editado.save()
            
            messages.success(request, "Producto actualizado correctamente.")
            return redirect('listar_productos')
    else:
        form = ProductoEditableForm(instance=producto)

    context = {
        'form': form
    }
    return render(request, 'productos/form_producto.html', context)

def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, 'Producto eliminado correctamente.')
    return redirect('listar_productos')