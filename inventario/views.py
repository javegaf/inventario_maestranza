"""
Vistas del módulo inventario: productos, 
movimientos, proveedores, kits, alertas, reportes y precios.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from .models import Producto, MovimientoInventario, Proveedor, KitProducto, HistorialPrecio, AlertaStock, AuditoriaInventario
from .forms import ProductoForm, MovimientoInventarioForm, ProveedorForm, KitProductoForm
from django.db.models import Q
from .forms import MovimientoFiltroForm
import datetime
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Productos

def lista_productos(request):
    """Muestra la lista de productos registrados en el sistema."""
    productos = Producto.objects.all()
    
    # Add audit information
    for producto in productos:
        producto.block_status = producto.is_blocked
    
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
    """Muestra el historial de movimientos de inventario con capacidad de filtrado."""
    # Start with all movements
    movimientos = MovimientoInventario.objects.all().order_by('-fecha')
    
    # Initialize the filter form
    form = MovimientoFiltroForm(request.GET or None)
    
    # Apply filters if form is valid
    if form.is_valid():
        # Filter by date range
        if form.cleaned_data.get('fecha_inicio'):
            fecha_inicio = form.cleaned_data['fecha_inicio']
            movimientos = movimientos.filter(fecha__gte=datetime.datetime.combine(fecha_inicio, datetime.time.min))
        
        if form.cleaned_data.get('fecha_fin'):
            fecha_fin = form.cleaned_data['fecha_fin']
            movimientos = movimientos.filter(fecha__lte=datetime.datetime.combine(fecha_fin, datetime.time.max))
        
        # Filter by movement type
        if form.cleaned_data.get('tipo_movimiento'):
            movimientos = movimientos.filter(tipo=form.cleaned_data['tipo_movimiento'])
        
        # Filter by product
        if form.cleaned_data.get('producto'):
            movimientos = movimientos.filter(producto=form.cleaned_data['producto'])
    
    return render(request, 'movimientos/lista_movimientos.html', {
        'movimientos': movimientos,
        'filtro_form': form
    })

def crear_movimiento(request):
    """Formulario para registrar un nuevo movimiento de inventario."""
    form = MovimientoInventarioForm(request.POST or None)
    
    if form.is_valid():
        producto = form.cleaned_data['producto']
        
        # Check if product is blocked
        if producto.is_blocked:
            form.add_error('producto', 'Este producto está bloqueado y no puede ser modificado.')
        else:
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

def historial_bloqueos(request):
    """Muestra el historial de bloqueos y desbloqueos de productos."""
    auditorias = AuditoriaInventario.objects.all().order_by('-fecha_inicio')
    return render(request, 'productos/historial_bloqueos.html', {'auditorias': auditorias})

@login_required
def toggle_block_product(request, producto_id):
    """Toggle the blocked status of a product."""
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Check if there's an active block for this product
    auditoria_activa = AuditoriaInventario.objects.filter(
        producto=producto, 
        bloqueado=True
    ).first()
    
    if auditoria_activa:
        # Unblock the product
        auditoria_activa.finalizar()
        mensaje = f"Producto '{producto.nombre}' desbloqueado exitosamente."
        estado = False
    else:
        # Block the product
        motivo = request.POST.get('motivo', 'Bloqueado por auditoría o mantenimiento')
        AuditoriaInventario.objects.create(
            producto=producto,
            bloqueado=True,
            motivo=motivo,
            usuario_auditor=request.user
        )
        mensaje = f"Producto '{producto.nombre}' bloqueado exitosamente."
        estado = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': mensaje,
            'blocked': estado
        })
    
    return redirect('listar_productos')
