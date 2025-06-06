"""
Vistas del módulo inventario: productos, 
movimientos, proveedores, kits, alertas, reportes y precios.
"""

import csv
import datetime
from io import BytesIO

from django.db import models
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template.loader import get_template
from xhtml2pdf import pisa

from .forms import (
    KitProductoForm, MovimientoFiltroForm, MovimientoInventarioForm,
    ProductoForm, ProveedorForm
)
from .models import (
    AlertaStock, HistorialPrecio, InformeInventario,
    KitProducto, MovimientoInventario, Producto, Proveedor
)

# Productos

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'productos/lista_productos.html', {'productos': productos})

def crear_producto(request):
    form = ProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('listar_productos')
    return render(request, 'productos/formulario_producto.html', {'form': form})

# Movimientos

def lista_movimientos(request):
    movimientos = MovimientoInventario.objects.all().order_by('-fecha')
    form = MovimientoFiltroForm(request.GET or None)

    if form.is_valid():
        if form.cleaned_data.get('fecha_inicio'):
            fecha_inicio = form.cleaned_data['fecha_inicio']
            movimientos = movimientos.filter(
                fecha__gte=datetime.datetime.combine(fecha_inicio, datetime.time.min))
        if form.cleaned_data.get('fecha_fin'):
            fecha_fin = form.cleaned_data['fecha_fin']
            movimientos = movimientos.filter(
                fecha__lte=datetime.datetime.combine(fecha_fin, datetime.time.max))
        if form.cleaned_data.get('tipo_movimiento'):
            movimientos = movimientos.filter(tipo=form.cleaned_data['tipo_movimiento'])
        if form.cleaned_data.get('producto'):
            movimientos = movimientos.filter(producto=form.cleaned_data['producto'])

    return render(request, 'movimientos/lista_movimientos.html', {
        'movimientos': movimientos,
        'filtro_form': form
    })

def crear_movimiento(request):
    form = MovimientoInventarioForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_movimientos')
    return render(request, 'movimientos/formulario_movimiento.html', {'form': form})

# Proveedores

def lista_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'proveedores/lista_proveedores.html', {'proveedores': proveedores})

def crear_proveedor(request):
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_proveedores')
    return render(request, 'proveedores/formulario_proveedor.html', {'form': form})

# Alertas de stock

def alertas_stock(request):
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
        alerta, _ = AlertaStock.objects.get_or_create(
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
    kits = KitProducto.objects.all()
    return render(request, 'kits/lista_kits.html', {'kits': kits})

def crear_kit(request):
    form = KitProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_kits')
    return render(request, 'kits/formulario_kit.html', {'form': form})

# Reportes

def reportes(request):
    informes = InformeInventario.objects.all().order_by('-fecha_generacion')
    movimientos = MovimientoInventario.objects.select_related('producto').order_by('-fecha')[:50]
    return render(request, 'reportes/reportes.html', {
        'reportes': informes,
        'movimientos': movimientos
    })

def exportar_csv(request):
    try:
        movimientos = MovimientoInventario.objects.select_related('producto').all()
        ahora = datetime.datetime.now()
        fecha_str = ahora.strftime('%Y-%m-%d_%H-%M')
        nombre_archivo = f'reporte_inventario_{fecha_str}.csv'

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'

        writer = csv.writer(response)
        writer.writerow(['Producto', 'Tipo', 'Cantidad', 'Fecha'])

        for m in movimientos:
            writer.writerow([
                m.producto.nombre,
                m.get_tipo_display(),
                m.cantidad,
                m.fecha.strftime('%d/%m/%Y %H:%M')
            ])

        InformeInventario.objects.create(
            nombre=nombre_archivo,
            fecha_generacion=ahora
        )

        return response

    except Exception as e:
        return HttpResponse(f"Error al generar el CSV: {str(e)}", status=500)

def exportar_pdf(request):
    movimientos = MovimientoInventario.objects.select_related('producto').all()
    ahora = datetime.datetime.now()
    fecha_str = ahora.strftime('%Y-%m-%d_%H-%M')

    try:
        template = get_template('reportes/reporte_pdf.html')
        html = template.render({'movimientos': movimientos, 'ahora': ahora})
        
        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html.encode('UTF-8')), dest=buffer, encoding='UTF-8')
        if pisa_status.err:
            return HttpResponse("Error al generar PDF", status=500)

        InformeInventario.objects.create(
            nombre=f'reporte_inventario_{fecha_str}.pdf',
            fecha_generacion=ahora
        )

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_inventario_{fecha_str}.pdf"'
        return response

    except Exception as e:
        return HttpResponse(f"Error al generar el PDF: {str(e)}", status=500)

# Historial de precios

def historial_precios(request):
    historial = HistorialPrecio.objects.all()
    return render(request, 'precios/historial_precios.html', {'historial': historial})
