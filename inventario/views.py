"""
Vistas del módulo inventario: productos, 
movimientos, proveedores, kits, alertas, reportes y precios.
"""

import csv
import datetime
import logging

from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import F, Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import get_template
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils import timezone
from xhtml2pdf import pisa

from .models import (
    Producto, MovimientoInventario, Proveedor, KitProducto,
    HistorialPrecio, AlertaStock, AuditoriaInventario, CompraProveedor,
    EvaluacionProveedor, InformeInventario, LoteProducto, HistorialLote
)
from .forms import (
    ProductoForm, ProductoEditableForm, MovimientoInventarioForm,
    MovimientoFiltroForm, ProveedorForm, KitProductoForm,
    CompraProveedorForm, EvaluacionProveedorForm, LoteProductoForm, LoteFiltroForm
)

logger = logging.getLogger(__name__)

# Productos

def lista_productos(request):
    productos = Producto.objects.all()
    for producto in productos:
        producto.block_status = producto.is_blocked
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

    # Check if non-staff user is trying to access movement creation
    show_permission_alert = False
    if request.user.is_authenticated and not request.user.is_staff:
        # Log the attempt if they're trying to create movements
        if 'create_attempt' in request.GET:
            logger.warning(f"Non-staff user {request.user.username} (ID: {request.user.id}) attempted to create movement at {timezone.now()}")
        show_permission_alert = True

    if form.is_valid():
        if form.cleaned_data.get('fecha_inicio'):
            fecha_inicio = form.cleaned_data['fecha_inicio']
            movimientos = movimientos.filter(fecha__gte=datetime.datetime.combine(fecha_inicio, datetime.time.min))
        if form.cleaned_data.get('fecha_fin'):
            fecha_fin = form.cleaned_data['fecha_fin']
            movimientos = movimientos.filter(fecha__lte=datetime.datetime.combine(fecha_fin, datetime.time.max))
        if form.cleaned_data.get('tipo_movimiento'):
            movimientos = movimientos.filter(tipo=form.cleaned_data['tipo_movimiento'])
        if form.cleaned_data.get('producto'):
            movimientos = movimientos.filter(producto=form.cleaned_data['producto'])

    return render(request, 'movimientos/lista_movimientos.html', {
        'movimientos': movimientos,
        'filtro_form': form,
        'show_permission_alert': show_permission_alert
    })

# Keep crear_movimiento unchanged for now - it can still be accessed directly
def crear_movimiento(request):
    """Vista para crear un nuevo movimiento de inventario."""
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            if producto.is_blocked:
                form.add_error('producto', 'Este producto está bloqueado y no puede ser modificado.')
            else:
                movimiento = form.save(commit=False)
                movimiento.usuario = request.user
                movimiento.save()  # This will trigger the save method that updates quantities
                messages.success(request, 'Movimiento creado exitosamente.')
                return redirect('lista_movimientos')
    else:
        form = MovimientoInventarioForm()
    
    return render(request, 'movimientos/formulario_movimiento.html', {'form': form})

# Proveedores

def lista_proveedores(request):
    proveedores = Proveedor.objects.filter(activo=True).annotate(total_compras=models.Count('compras'))
    return render(request, 'proveedores/lista_proveedores.html', {'proveedores': proveedores})

def crear_proveedor(request):
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_proveedores')
    return render(request, 'proveedores/formulario_proveedor.html', {'form': form, 'action': 'Crear'})

def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid():
        form.save()
        return redirect('lista_proveedores')
    return render(request, 'proveedores/formulario_proveedor.html', {
        'form': form, 'proveedor': proveedor, 'action': 'Editar'
    })

def detalle_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    compras = CompraProveedor.objects.filter(proveedor=proveedor).order_by('-fecha_compra')
    evaluaciones = EvaluacionProveedor.objects.filter(proveedor=proveedor).order_by('-fecha_evaluacion')
    return render(request, 'proveedores/detalle_proveedor.html', {
        'proveedor': proveedor, 'compras': compras, 'evaluaciones': evaluaciones
    })

@login_required
def registrar_compra(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == 'POST':
        form = CompraProveedorForm(request.POST)
        if form.is_valid():
            compra = form.save(commit=False)
            compra.proveedor = proveedor
            compra.usuario = request.user
            compra.save()
            producto = compra.producto
            producto.stock_actual += compra.cantidad
            producto.save()
            return redirect('detalle_proveedor', proveedor_id=proveedor.id)
    else:
        form = CompraProveedorForm(initial={'proveedor': proveedor})
    return render(request, 'proveedores/formulario_compra.html', {'form': form, 'proveedor': proveedor})

@login_required
def evaluar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    form = EvaluacionProveedorForm(request.POST or None)
    if form.is_valid():
        evaluacion = form.save(commit=False)
        evaluacion.proveedor = proveedor
        evaluacion.usuario = request.user
        evaluacion.save()
        return redirect('detalle_proveedor', proveedor_id=proveedor.id)
    return render(request, 'proveedores/formulario_evaluacion.html', {'form': form, 'proveedor': proveedor})

# Alertas

def alertas_stock(request):
    """Muestra productos cuyo stock actual está por debajo del mínimo definido."""
    productos_bajo_stock = Producto.objects.filter(stock_actual__lt=models.F('stock_minimo'))
    
    print(f"DEBUG: Found {productos_bajo_stock.count()} products with low stock")
    
    # Handle mark as attended action
    if request.method == 'POST' and 'alerta_id' in request.POST:
        alerta_id = request.POST.get('alerta_id')
        try:
            alerta = AlertaStock.objects.get(id=alerta_id)
            alerta.atendido = True
            alerta.save()
            return redirect('alertas_stock')
        except AlertaStock.DoesNotExist:
            pass
    
    # Check for new alerts and send emails automatically
    nuevas_alertas = []
    for producto in productos_bajo_stock:
        print(f"DEBUG: Checking product {producto.nombre} - Stock: {producto.stock_actual}, Min: {producto.stock_minimo}")
        
        # Check if there's already an active (unattended) alert for this product
        alerta_existente = AlertaStock.objects.filter(
            producto=producto,
            atendido=False
        ).first()
        
        print(f"DEBUG: Existing alert for {producto.nombre}: {alerta_existente}")
        
        if not alerta_existente:
            # Create new alert only if no unattended alert exists
            nueva_alerta = AlertaStock.objects.create(
                producto=producto,
                mensaje=f'El producto {producto.nombre} tiene un stock de {producto.stock_actual} unidades, por debajo del mínimo de {producto.stock_minimo}.',
                atendido=False
            )
            nuevas_alertas.append(nueva_alerta)
            print(f"DEBUG: Created new alert for {producto.nombre}")
    
    print(f"DEBUG: Total new alerts to send: {len(nuevas_alertas)}")
    
    # Send email for new alerts
    if nuevas_alertas:
        try:
            print("DEBUG: Attempting to send email...")
            enviar_alerta_automatica(nuevas_alertas)
            print(f"DEBUG: Email sent successfully for {len(nuevas_alertas)} alerts")
            logger.info(f"Automatic email sent for {len(nuevas_alertas)} new low stock alerts")
        except Exception as e:
            print(f"DEBUG: Error sending email: {str(e)}")
            logger.error(f"Error sending automatic email: {str(e)}")
    else:
        print("DEBUG: No new alerts to send")
    
    # Get all unattended alerts
    todas_alertas = AlertaStock.objects.filter(atendido=False).order_by('-fecha_alerta')
    print(f"DEBUG: Total unattended alerts: {todas_alertas.count()}")
    
    return render(request, 'alertas/alertas_stock.html', {
        'productos_bajo_stock': productos_bajo_stock,
        'alertas': todas_alertas
    })

def enviar_alerta_automatica(alertas):
    """Envía alertas automáticas por email a usuarios staff."""
    
    print("DEBUG: Starting email sending process...")
    
    # Email configuration
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'sistema@empresa.com')
    
    # Get only staff users with email addresses
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    staff_users = User.objects.filter(
        is_active=True,
        is_staff=True,  # Only staff users
        email__isnull=False
    ).exclude(email='')
    
    recipient_list = [user.email for user in staff_users]
    
    print(f"DEBUG: From email: {from_email}")
    print(f"DEBUG: Found {len(recipient_list)} staff users with email")
    print(f"DEBUG: Recipients: {recipient_list}")
    
    if not recipient_list:
        print("DEBUG: No staff users with email found!")
        return
    
    # Prepare email content
    if len(alertas) == 1:
        subject = f'🚨 ALERTA: {alertas[0].producto.nombre} - Stock Bajo'
    else:
        subject = f'🚨 ALERTA: {len(alertas)} productos con stock bajo'
    
    print(f"DEBUG: Email subject: {subject}")
    
    message_lines = [
        'ALERTA AUTOMÁTICA DE STOCK BAJO',
        f'Fecha: {timezone.now().strftime("%d/%m/%Y %H:%M")}',
        '',
        f'Se han detectado {len(alertas)} nuevos productos con stock por debajo del mínimo:',
        '',
    ]
    
    for alerta in alertas:
        producto = alerta.producto
        deficit = producto.stock_minimo - producto.stock_actual
        
        status = '🔴 SIN STOCK' if producto.stock_actual == 0 else '🟡 STOCK BAJO'
        
        message_lines.extend([
            f'{status} - {producto.nombre}',
            f'   Stock actual: {producto.stock_actual}',
            f'   Stock mínimo: {producto.stock_minimo}',
            f'   Déficit: {deficit} unidades',
            ''
        ])
    
    message_lines.extend([
        '⚠️ ACCIÓN REQUERIDA:',
        '• Revisar inventario',
        '• Gestionar pedidos urgentes',
        '• Coordinar con proveedores',
        '',
        '---',
        'Mensaje automático del Sistema de Inventario.',
    ])
    
    message = '\n'.join(message_lines)
    
    print("DEBUG: Email message prepared:")
    print("=" * 50)
    print(message)
    print("=" * 50)
    
    # Send email
    try:
        print("DEBUG: Calling send_mail...")
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,  # Change this to False to see errors
        )
        print("DEBUG: send_mail completed successfully!")
    except Exception as e:
        print(f"DEBUG: send_mail failed with error: {str(e)}")
        raise e

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
        'reportes': informes, 'movimientos': movimientos
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
        InformeInventario.objects.create(nombre=nombre_archivo, fecha_generacion=ahora)
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
        InformeInventario.objects.create(nombre=f'reporte_inventario_{fecha_str}.pdf', fecha_generacion=ahora)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_inventario_{fecha_str}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error al generar el PDF: {str(e)}", status=500)

# Historial

def historial_precios(request):
    historial = HistorialPrecio.objects.all()
    return render(request, 'precios/historial_precios.html', {'historial': historial})

def historial_bloqueos(request):
    auditorias = AuditoriaInventario.objects.all().order_by('-fecha_inicio')
    return render(request, 'productos/historial_bloqueos.html', {'auditorias': auditorias})

@login_required
def toggle_block_product(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    auditoria_activa = AuditoriaInventario.objects.filter(producto=producto, bloqueado=True).first()
    if auditoria_activa:
        auditoria_activa.finalizar()
        mensaje = f"Producto '{producto.nombre}' desbloqueado exitosamente."
        estado = False
    else:
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
        return JsonResponse({'status': 'success', 'message': mensaje, 'blocked': estado})
    return redirect('listar_productos')

# Dashboard y edición

@login_required
def dashboard_inventario(request):
    total_productos = Producto.objects.count()
    productos_sin_stock = Producto.objects.filter(stock_actual=0).count()
    productos_bajo_minimo = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).count()
    movimientos = MovimientoInventario.objects.values('tipo').annotate(total=Count('id')).order_by('tipo')
    tipos = [m['tipo'].capitalize() for m in movimientos]
    cantidades = [m['total'] for m in movimientos]
    colores_contexto = {
        'Entrada': 'rgba(75, 192, 192, 0.6)',
        'Salida': 'rgba(255, 99, 132, 0.6)',
        'Ajuste': 'rgba(255, 206, 86, 0.6)',
        'Devolucion': 'rgba(54, 162, 235, 0.6)',
    }
    colores_barras = [colores_contexto.get(tipo.capitalize(), 'rgba(153, 102, 255, 0.6)') for tipo in tipos]
    alertas_stock = AlertaStock.objects.filter(atendido=False).select_related('producto').order_by('-fecha_alerta')
    proveedores = Producto.objects.values('proveedor__nombre').annotate(total=Count('id')).order_by('-total')
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
    return render(request, 'productos/form_producto.html', {'form': form})

def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, 'Producto eliminado correctamente.')
    return redirect('listar_productos')

@login_required
def detalle_producto_lotes(request, producto_id):
    """Vista para mostrar los lotes de un producto específico."""
    producto = get_object_or_404(Producto, id=producto_id)
    lotes = LoteProducto.objects.filter(producto=producto, activo=True).order_by('fecha_vencimiento')
    
    # Add calculated fields to each lote
    for lote in lotes:
        if lote.dias_hasta_vencimiento < 0:
            lote.dias_vencido = abs(lote.dias_hasta_vencimiento)
        else:
            lote.dias_vencido = 0
    
    # Apply filters
    form = LoteFiltroForm(request.GET or None)
    if form.is_valid():
        estado = form.cleaned_data.get('estado')
        if estado == 'vencido':
            lotes = lotes.filter(fecha_vencimiento__lt=timezone.now().date())
        elif estado == 'por_vencer':
            fecha_limite = timezone.now().date() + datetime.timedelta(days=30)
            lotes = lotes.filter(fecha_vencimiento__lte=fecha_limite, fecha_vencimiento__gte=timezone.now().date())
        elif estado == 'activo':
            lotes = lotes.filter(fecha_vencimiento__gte=timezone.now().date())
            
        if form.cleaned_data.get('fecha_vencimiento_desde'):
            lotes = lotes.filter(fecha_vencimiento__gte=form.cleaned_data['fecha_vencimiento_desde'])
        if form.cleaned_data.get('fecha_vencimiento_hasta'):
            lotes = lotes.filter(fecha_vencimiento__lte=form.cleaned_data['fecha_vencimiento_hasta'])
    
    return render(request, 'productos/detalle_lotes.html', {
        'producto': producto,
        'lotes': lotes,
        'filtro_form': form
    })

@login_required
def crear_lote(request, producto_id):
    """Vista para crear un nuevo lote."""
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = LoteProductoForm(request.POST, producto=producto)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.save()
            
            # Create history record with user information
            HistorialLote.objects.create(
                lote=lote,
                tipo_cambio='creacion',
                cantidad_anterior=0,
                cantidad_nueva=lote.cantidad_inicial,
                usuario=request.user,  # Add the current user
                observaciones=f'Lote creado con {lote.cantidad_inicial} unidades por {request.user.username}'
            )
            
            messages.success(request, f'Lote {lote.numero_lote} creado exitosamente.')
            return redirect('detalle_producto_lotes', producto_id=producto.id)
    else:
        form = LoteProductoForm(producto=producto)
    
    return render(request, 'productos/formulario_lote.html', {
        'form': form,
        'producto': producto,
        'action': 'Crear'
    })

@login_required
def historial_lotes(request, lote_id=None):
    """Vista para mostrar el historial de lotes."""
    if lote_id:
        lote = get_object_or_404(LoteProducto, id=lote_id)
        historial = HistorialLote.objects.filter(lote=lote)
        titulo = f'Historial del Lote {lote.numero_lote}'
    else:
        historial = HistorialLote.objects.all()
        lote = None
        titulo = 'Historial de Todos los Lotes'
    
    return render(request, 'productos/historial_lotes.html', {
        'historial': historial,
        'lote': lote,
        'titulo': titulo
    })

@login_required
def editar_lote(request, lote_id):
    """Vista para editar un lote."""
    lote = get_object_or_404(LoteProducto, id=lote_id)
    
    if request.method == 'POST':
        cantidad_anterior = lote.cantidad_actual
        form = LoteProductoForm(request.POST, instance=lote, producto=lote.producto)
        if form.is_valid():
            lote_editado = form.save()
            
            # Create history record if quantity changed
            if cantidad_anterior != lote_editado.cantidad_actual:
                HistorialLote.objects.create(
                    lote=lote_editado,
                    tipo_cambio='uso',
                    cantidad_anterior=cantidad_anterior,
                    cantidad_nueva=lote_editado.cantidad_actual,
                    usuario=request.user,  # Current user making the edit
                    observaciones=f'Cantidad modificada de {cantidad_anterior} a {lote_editado.cantidad_actual} por {request.user.username}'
                )
            
            messages.success(request, f'Lote {lote.numero_lote} actualizado exitosamente.')
            return redirect('detalle_producto_lotes', producto_id=lote.producto.id)
    else:
        form = LoteProductoForm(instance=lote, producto=lote.producto)
    
    return render(request, 'productos/formulario_lote.html', {
        'form': form,
        'producto': lote.producto,
        'lote': lote,
        'action': 'Editar'
    })

@login_required
def api_producto_lotes(request, producto_id):
    """API endpoint to get lotes for a specific product."""
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        lotes = LoteProducto.objects.filter(producto=producto, activo=True).order_by('fecha_vencimiento')
        
        lotes_data = []
        for lote in lotes:
            lotes_data.append({
                'id': lote.id,
                'numero_lote': lote.numero_lote,
                'cantidad_actual': lote.cantidad_actual,
                'fecha_vencimiento': lote.fecha_vencimiento.strftime('%d/%m/%Y'),
                'esta_vencido': lote.esta_vencido
            })
        
        return JsonResponse({
            'lotes': lotes_data,
            'stock_total': producto.stock_actual
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)