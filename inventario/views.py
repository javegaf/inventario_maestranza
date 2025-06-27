"""
Vistas del módulo inventario: productos, 
movimientos, proveedores, kits, alertas, reportes y precios.
"""
# pylint: disable=C0302, W0718, W1203, C0103

# =====================================
# Imports estándar de Python
# =====================================
import csv
import datetime
import logging
from io import BytesIO

# =====================================
# Imports de Django
# =====================================
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db import models
from django.db.models import Count, F, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import get_template
from django.utils import timezone

# =====================================
# Imports de terceros
# =====================================
from xhtml2pdf import pisa

# =====================================
# Imports locales
# =====================================
from .utils import exportar_excel_inventario, exportar_pdf_inventario


from .models import (
    Producto, MovimientoInventario, Proveedor, KitProducto, ProductoEnKit,
    HistorialPrecio, AlertaStock, AuditoriaInventario, CompraProveedor,
    EvaluacionProveedor, InformeInventario, LoteProducto, HistorialLote,
    Proyecto, MaterialProyecto, AuditoriaInformeInventario, OrdenCompra, ItemOrdenCompra, OrdenCompraLog
)
from .forms import (
    ProductoForm, ProductoEditableForm, MovimientoInventarioForm,
    MovimientoFiltroForm, ProveedorForm, KitProductoForm,
    CompraProveedorForm, EvaluacionProveedorForm, LoteProductoForm, LoteFiltroForm,
    HistorialPrecioFiltroForm, RegistroPrecioManualForm, ProyectoForm,
    MaterialProyectoForm, ActualizarUsoMaterialForm,
    ConfiguracionSistemaForm, InformeInventarioFiltroForm, OrdenCompraFiltroForm
)

logger = logging.getLogger(__name__)
def is_staff(user):
    return user.is_staff
# Productos
def lista_productos(request):
    """Muestra la lista de productos registrados en el sistema."""
    # pylint: disable=no-member
    productos = Producto.objects.all()
    for producto in productos:
        producto.block_status = producto.is_blocked

    #para el filtrado
    nombre = request.GET.get('nombre', '')
    ubicacion = request.GET.get('ubicacion', '')
    categoria = request.GET.get('categoria', '')

    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if ubicacion:
        productos = productos.filter(ubicacion__icontains=ubicacion)
    if categoria:
        productos = productos.filter(categoria__icontains=categoria)

    # Obtener categorías únicas para el filtro
    categorias = Producto.objects.values_list('categoria', flat=True).distinct()

    # Paginador: 5 productos por página
    paginator = Paginator(productos, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'categorias': categorias,
        'request': request,
        'productos': productos
    }

    return render(request, 'productos/lista_productos.html', context)

@login_required
def crear_producto(request):
    """Vista para crear un nuevo producto."""
    form = ProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('listar_productos')
    return render(request, 'productos/formulario_producto.html', {'form': form})

@login_required
def editar_producto(request, producto_id):
    """Vista para editar un producto existente."""
    producto = get_object_or_404(Producto, id=producto_id)
    fecha_actual = producto.fecha_vencimiento

    if request.method == 'POST':
        form = ProductoEditableForm(request.POST, instance=producto)
        if form.is_valid():
            producto_editado = form.save(commit=False)
            if not form.cleaned_data.get('fecha_vencimiento'):
                producto_editado.fecha_vencimiento = fecha_actual
            producto_editado.save()
            # Actualizar el stock mínimo en las alertas
            
            if producto.stock_minimo > 0:
                # pylint: disable=no-member
                mensaje_alerta = f"Stock mínimo actualizado: {producto_editado.stock_minimo}"
                AlertaStock.objects.update_or_create(
                    producto=producto_editado,
                    atendido=False,
                    defaults={
                        'mensaje': mensaje_alerta,
                        'fecha_alerta': timezone.now()
                    }
                )

            messages.success(request, "Producto actualizado correctamente.")
            return redirect('inventario:listar_productos')
    else:
        form = ProductoEditableForm(instance=producto)

    return render(request, 'productos/form_producto.html', {'form': form})

@login_required
def eliminar_producto(request, producto_id):
    """Vista para eliminar un producto existente."""
    producto = get_object_or_404(Producto, id=producto_id)

    # Revisa si existen lotes o movimientos asociados al producto
    # pylint: disable=no-member
    lotes_existentes = LoteProducto.objects.filter(producto=producto).exists()
    movimientos_existentes = MovimientoInventario.objects.filter(producto=producto).exists()

    if request.method == 'POST':
        if 'confirmar' in request.POST:
            nombre_producto = producto.nombre

            try:
                producto.delete()
                messages.success(request, f'Producto "{nombre_producto}" eliminado correctamente.')
            except Exception as e:
                messages.error(request, f'Error al eliminar el producto: {e}')

            return redirect('inventario:listar_productos')  # Add namespace

    return render(request, 'productos/confirmar_eliminar_producto.html', {
        'producto': producto,
        'lotes_existentes': lotes_existentes,
        'movimientos_existentes': movimientos_existentes,
    })

# Movimientos


def lista_movimientos(request):
    """Vista para listar los movimientos de inventario con filtros."""
    # pylint: disable=no-member
    
    form = MovimientoFiltroForm(request.GET or None)
    movimientos_qs = MovimientoInventario.objects.all().order_by('-fecha')
    movimientos = movimientos_qs  # por defecto
    # Revisa si el usuario es staff o no
    show_permission_alert = False
    if request.user.is_authenticated and not request.user.is_staff:
        # Revisar si el usuario intentó crear un movimiento
        if 'create_attempt' in request.GET:
            logger.warning(
            "Non-staff user %s (ID: %s) attempted to create movement at %s",
            request.user.username,
            request.user.id,
            timezone.now())
            show_permission_alert = True

    if form.is_valid():
        if form.cleaned_data.get('fecha_inicio'):
            fecha_inicio = form.cleaned_data['fecha_inicio']
            movimientos_qs = movimientos.filter(
                fecha__gte=datetime.datetime.combine(fecha_inicio, datetime.time.min))
        if form.cleaned_data.get('fecha_fin'):
            fecha_fin = form.cleaned_data['fecha_fin']
            movimientos_qs = movimientos.filter(
                fecha__lte=datetime.datetime.combine(fecha_fin, datetime.time.max))
        if form.cleaned_data.get('tipo_movimiento'):
            movimientos_qs = movimientos.filter(tipo=form.cleaned_data['tipo_movimiento'])
        if form.cleaned_data.get('producto'):
            movimientos_qs = movimientos.filter(producto=form.cleaned_data['producto'])
        if form.cleaned_data.get('usuario'):
            movimientos_qs = movimientos.filter(usuario=form.cleaned_data['usuario'])
    # Paginación
    paginator = Paginator(movimientos_qs, 5)
    page_number = request.GET.get('page')
    try:
        movimientos = paginator.page(page_number)
    except PageNotAnInteger:
        movimientos = paginator.page(1)
    except EmptyPage:
        movimientos = paginator.page(paginator.num_pages)

    # Excluir 'page' del querystring para mantener filtros
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    querystring = query_params.urlencode()
    return render(request, 'movimientos/lista_movimientos.html', {
        'movimientos': movimientos,
        'filtro_form': form,
        'show_permission_alert': show_permission_alert,
        'querystring': querystring
    })
# Keep crear_movimiento unchanged for now - it can still be accessed directly
def crear_movimiento(request):
    """Vista para crear un nuevo movimiento de inventario."""
    if request.method == 'POST':
        form = MovimientoInventarioForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            if producto.is_blocked:
                form.add_error('producto',
                               'Este producto está bloqueado y no puede ser modificado.')
            else:
                movimiento = form.save(commit=False)
                movimiento.usuario = request.user
                movimiento.save()  # This will trigger the save method that updates quantities
                messages.success(request, 'Movimiento creado exitosamente.')
                return redirect('inventario:lista_movimientos')  # ← Updated with namespace
    else:
        form = MovimientoInventarioForm()

    return render(request, 'movimientos/formulario_movimiento.html', {'form': form})

# Proveedores

def lista_proveedores(request):
    """Vista mejorada con información de precios."""
    # pylint: disable=no-member
    proveedores_base = Proveedor.objects.filter(activo=True).annotate(
        total_compras=models.Count('compras')
    )

    # Construir una lista de proveedores con estadísticas de precios
    proveedores = []
    for proveedor in proveedores_base:
        # Toma el historial de precios del proveedor
        historial = HistorialPrecio.objects.filter(proveedor=proveedor)

        if historial.exists():
            precio_promedio = historial.aggregate(avg=models.Avg('precio_unitario'))['avg']
            productos_suministrados = historial.values('producto').distinct().count()
        else:
            precio_promedio = None
            productos_suministrados = 0

        # Añade el proveedor a la lista
        proveedor.precio_promedio = precio_promedio
        proveedor.productos_suministrados = productos_suministrados
        proveedores.append(proveedor)

    return render(request, 'proveedores/lista_proveedores.html', {'proveedores': proveedores})

def crear_proveedor(request):
    """Vista para crear un nuevo proveedor."""
    form = ProveedorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('inventario:lista_proveedores')
    return render(
        request, 'proveedores/formulario_proveedor.html', {
            'form': form, 'action': 'Crear'})

def editar_proveedor(request, proveedor_id):
    """Vista para editar un proveedor existente."""
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    form = ProveedorForm(request.POST or None, instance=proveedor)
    if form.is_valid():
        form.save()
        return redirect('inventario:lista_proveedores')
    return render(request, 'proveedores/formulario_proveedor.html', {
        'form': form, 'proveedor': proveedor, 'action': 'Editar'
    })

def detalle_proveedor(request, proveedor_id):
    """Vista mejorada con información de precios."""
    # pylint: disable=no-member
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    compras = CompraProveedor.objects.filter(proveedor=proveedor).order_by('-fecha_compra')
    evaluaciones = EvaluacionProveedor.objects.filter(
        proveedor=proveedor).order_by('-fecha_evaluacion')

    # Rescatar historial de precios del proveedor
    # pylint: disable=no-member
    historial = HistorialPrecio.objects.filter(proveedor=proveedor)
    precio_stats = None
    ultimos_precios = {}

    if historial.exists():
        # calcula estadísticas de precios
        precio_stats = {
            'precio_promedio_general': historial.aggregate(
                avg_precio=models.Avg('precio_unitario'))['avg_precio'] or 0,
            'productos_suministrados': historial.values('producto').distinct().count(),
            'total_transacciones': historial.count(),
            'precio_minimo': historial.aggregate(
                min_precio=models.Min('precio_unitario'))['min_precio'] or 0,
            'precio_maximo': historial.aggregate(
                max_precio=models.Max('precio_unitario'))['max_precio'] or 0,
        }

        # obtener los últimos precios de cada producto
        productos = historial.values('producto').distinct()
        for producto_info in productos:
            # pylint: disable=no-member
            producto_id = producto_info['producto']
            producto = Producto.objects.get(id=producto_id)
            precios_producto = historial.filter(producto=producto).order_by('-fecha')

            if precios_producto.count() >= 1:
                ultimo_precio = precios_producto.first()
                variacion = 0

                # Calculate price variation if we have at least 2 prices
                if precios_producto.count() >= 2:
                    precio_anterior = precios_producto[1].precio_unitario
                    if precio_anterior > 0:
                        variacion = ((
                            ultimo_precio.precio_unitario - precio_anterior
                            ) / precio_anterior) * 100

                ultimos_precios[producto.nombre] = {
                    'precio': ultimo_precio.precio_unitario,
                    'fecha': ultimo_precio.fecha,
                    'variacion': variacion
                }

    return render(request, 'proveedores/detalle_proveedor.html', {
        'proveedor': proveedor, 
        'compras': compras, 
        'evaluaciones': evaluaciones,
        'precio_stats': precio_stats,
        'ultimos_precios': ultimos_precios
    })

@login_required
def registrar_compra(request, proveedor_id):
    """Vista para registrar una compra de un proveedor."""
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
    return render(
        request, 'proveedores/formulario_compra.html', {
            'form': form, 'proveedor': proveedor})

@login_required
def evaluar_proveedor(request, proveedor_id):
    """Vista para registrar una evaluación de un proveedor."""
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    form = EvaluacionProveedorForm(request.POST or None)
    if form.is_valid():
        evaluacion = form.save(commit=False)
        evaluacion.proveedor = proveedor
        evaluacion.usuario = request.user
        evaluacion.save()
        return redirect('inventario:detalle_proveedor', proveedor_id=proveedor.id)
    return render(
        request, 'proveedores/formulario_evaluacion.html', {
            'form': form, 'proveedor': proveedor})

# Alertas

def alertas_stock(request):
    """Muestra productos cuyo stock actual está por debajo del mínimo definido."""
    # pylint: disable=no-member
    productos_bajo_stock = Producto.objects.filter(stock_actual__lt=models.F('stock_minimo'))
    print(f"DEBUG: Found {productos_bajo_stock.count()} products with low stock")
    # Marcar como atendidas las alertas si se recibe un POST con alerta_id
    if request.method == 'POST' and 'alerta_id' in request.POST:
        # pylint: disable=no-member
        alerta_id = request.POST.get('alerta_id')
        try:
            alerta = AlertaStock.objects.get(id=alerta_id)
            alerta.atendido = True
            alerta.save()
            return redirect('inventario:alertas_stock')
        except AlertaStock.DoesNotExist:
            pass

    # Revisa por nuevas alertas de stock bajo
    nuevas_alertas = []
    for producto in productos_bajo_stock:
        print(
        f"DEBUG: Checking product {producto.nombre} - "
        f"Stock: {producto.stock_actual}, Min: {producto.stock_minimo}"
)

        # Revisa si hay una alerta existente sin atender
        # pylint: disable=no-member
        alerta_existente = AlertaStock.objects.filter(
            producto=producto,
            atendido=False
        ).first()

        print(f"DEBUG: Existing alert for {producto.nombre}: {alerta_existente}")

        if not alerta_existente:
            # Crea una nueva alerta si no existe una sin atender
            # pylint: disable=no-member
            nueva_alerta = AlertaStock.objects.create(
                producto=producto,
                mensaje=(
                    f'El producto {producto.nombre} tiene un stock de '
                    f'{producto.stock_actual} unidades, por debajo del mínimo de '
                    f'{producto.stock_minimo}.'
                ),
                atendido=False
            )
            nuevas_alertas.append(nueva_alerta)
            print(f"DEBUG: Created new alert for {producto.nombre}")

    print(f"DEBUG: Total new alerts to send: {len(nuevas_alertas)}")

    # Envío de alertas automáticas por email
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

    # Obtener todas las alertas de stock sin atender
    todas_alertas = AlertaStock.objects.filter(atendido=False).order_by('-fecha_alerta')
    print(f"DEBUG: Total unattended alerts: {todas_alertas.count()}")

    return render(request, 'alertas/alertas_stock.html', {
        'productos_bajo_stock': productos_bajo_stock,
        'alertas': todas_alertas
    })

def enviar_alerta_automatica(alertas):
    """Envía alertas automáticas por email a usuarios staff."""
    print("DEBUG: Starting email sending process...")
    # Configurar el email desde settings o usar un valor por defecto
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'sistema@empresa.com')

    # Obtener usuarios staff activos con email
    User = get_user_model()

    staff_users = User.objects.filter(
        is_active=True,
        is_staff=True,
        email__isnull=False
    ).exclude(email='')

    recipient_list = [user.email for user in staff_users]

    print(f"DEBUG: From email: {from_email}")
    print(f"DEBUG: Found {len(recipient_list)} staff users with email")
    print(f"DEBUG: Recipients: {recipient_list}")

    if not recipient_list:
        print("DEBUG: No staff users with email found!")
        return

    # Prepara el asunto y mensaje del email
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

    # Enviar el email
    try:
        print("DEBUG: Calling send_mail...")
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        print("DEBUG: send_mail completed successfully!")
    except Exception as e:
        print(f"DEBUG: send_mail failed with error: {str(e)}")
        raise e

# Kits

def lista_kits(request):
    """Vista para listar los kits de productos."""
    # pylint: disable=no-member
    kits = KitProducto.objects.all()
    return render(request, 'kits/lista_kits.html', {'kits': kits})

def crear_kit(request):
    """Vista para crear un nuevo kit de productos."""
    form = KitProductoForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lista_kits')
    return render(request, 'kits/formulario_kit.html', {'form': form})

# Reportes

def reportes(request):
    """Vista para mostrar los reportes de inventario y movimientos recientes."""
    # pylint: disable=no-member
    informes = InformeInventario.objects.all().order_by('-fecha_generacion')
    movimientos = MovimientoInventario.objects.select_related('producto').order_by('-fecha')[:50]
    return render(request, 'reportes/reportes.html', {
        'reportes': informes, 'movimientos': movimientos
    })

def exportar_csv(request):# pylint: disable=unused-argument
    """Exporta los movimientos de inventario a un archivo CSV."""
    # pylint: disable=no-member
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
    except Exception as e: # pylint: disable=broad-except
        return HttpResponse(f"Error al generar el CSV: {str(e)}", status=500)

def exportar_pdf(request): # pylint: disable=unused-argument
    """Genera un reporte PDF de los movimientos de inventario."""
    # pylint: disable=no-member
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
            nombre=f'reporte_inventario_{fecha_str}.pdf', fecha_generacion=ahora)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="reporte_inventario_{fecha_str}.pdf"')
        return response
    except Exception as e: # pylint: disable=broad-except
        return HttpResponse(f"Error al generar el PDF: {str(e)}", status=500)

# Historial

def historial_precios(request):
    """Vista para mostrar el historial de precios con filtros."""
    # pylint: disable=no-member
    historial = HistorialPrecio.objects.select_related(
        'producto',
        'proveedor',
        'usuario',
        'compra').all()
    form = HistorialPrecioFiltroForm(request.GET or None)

    if form.is_valid():
        if form.cleaned_data.get('producto'):
            historial = historial.filter(producto=form.cleaned_data['producto'])
        if form.cleaned_data.get('proveedor'):
            historial = historial.filter(proveedor=form.cleaned_data['proveedor'])
        if form.cleaned_data.get('fecha_desde'):
            historial = historial.filter(fecha__gte=form.cleaned_data['fecha_desde'])
        if form.cleaned_data.get('fecha_hasta'):
            fecha_hasta = form.cleaned_data['fecha_hasta']
            # Añade el tiempo máximo del día
            fecha_hasta = datetime.datetime.combine(fecha_hasta, datetime.time.max)
            historial = historial.filter(fecha__lte=fecha_hasta)

    # Paginación
    paginator = Paginator(historial, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Calula estadísticas del historial
    stats = {
        'total_registros': historial.count(),
        'productos_unicos': historial.values('producto').distinct().count(),
        'proveedores_unicos': historial.values('proveedor').distinct().count(),
        'precio_promedio': historial.aggregate(
            avg_precio=models.Avg('precio_unitario'))['avg_precio'] or 0,
    }

    return render(request, 'precios/historial_precios.html', {
        'page_obj': page_obj,
        'filtro_form': form,
        'stats': stats
    })

def historial_precios_producto(request, producto_id):
    """Vista para mostrar el historial de precios de un producto específico."""
    # pylint: disable=no-member
    producto = get_object_or_404(Producto, id=producto_id)
    historial = HistorialPrecio.objects.filter(producto=producto).select_related(
        'proveedor', 'usuario', 'compra')

    # Calculate price evolution data for charts
    precios_data = []
    fechas_data = []
    proveedores_data = []
    colores_data = []

    colores_proveedores = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40']
    proveedores_unicos = {}
    color_index = 0

    for precio in historial:
        precios_data.append(float(precio.precio_unitario))
        fechas_data.append(precio.fecha.strftime('%d/%m/%Y'))
        proveedor_nombre = precio.proveedor.nombre if precio.proveedor else 'Sin proveedor'
        proveedores_data.append(proveedor_nombre)
        # Asigna color único a cada proveedor
        if proveedor_nombre not in proveedores_unicos:
            proveedores_unicos[proveedor_nombre] = colores_proveedores[
                color_index % len(colores_proveedores)]
            color_index += 1
        colores_data.append(proveedores_unicos[proveedor_nombre])

    # Toma los precios actuales y estadísticas
    if historial.exists():
        precio_actual = historial.first().precio_unitario
        precio_minimo = historial.aggregate(min_precio=models.Min('precio_unitario'))['min_precio']
        precio_maximo = historial.aggregate(max_precio=models.Max('precio_unitario'))['max_precio']
        precio_promedio = historial.aggregate(
            avg_precio=models.Avg('precio_unitario'))['avg_precio']

        # Calcula los precios de variación
        if historial.count() >= 2:
            primer_precio = historial.last().precio_unitario
            variacion_total = precio_actual - primer_precio
            porcentaje_variacion = (
                (precio_actual - primer_precio) / primer_precio
                ) * 100 if primer_precio > 0 else 0
        else:
            variacion_total = 0
            porcentaje_variacion = 0
    else:
        precio_actual = precio_minimo = precio_maximo = precio_promedio = 0
        variacion_total = porcentaje_variacion = 0

    stats = {
        'precio_actual': precio_actual,
        'precio_minimo': precio_minimo,
        'precio_maximo': precio_maximo,
        'precio_promedio': precio_promedio,
        'total_cambios': historial.count(),
        'variacion_total': variacion_total,
        'porcentaje_variacion': porcentaje_variacion,
        'tendencia': 'subida' 
        if variacion_total > 0 else 'bajada' if variacion_total < 0 else 'estable'
    }

    # Convierte proveedores_unicos a una lista de tuplas para el template
    proveedores_unicos_list = list(proveedores_unicos.items())

    return render(request, 'precios/historial_producto.html', {
        'producto': producto,
        'historial': historial,
        'stats': stats,
        'precios_data': precios_data,
        'fechas_data': fechas_data,
        'proveedores_data': proveedores_data,
        'colores_data': colores_data,
        'proveedores_unicos': proveedores_unicos_list,
    })

def historial_precios_proveedor(request, proveedor_id):
    """Vista para mostrar el historial de precios por proveedor."""
    # pylint: disable=no-member
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    historial = HistorialPrecio.objects.filter(
        proveedor=proveedor).select_related(
            'producto', 'usuario', 'compra')

    # Agrupa precios por producto
    productos_precios = {}
    for precio in historial:
        producto_nombre = precio.producto.nombre
        if producto_nombre not in productos_precios:
            productos_precios[producto_nombre] = {
                'producto': precio.producto,
                'precios': [],
                'precio_actual': None,
                'precio_anterior': None,
                'precio_promedio': None,
                'variacion': None,
                'porcentaje_variacion': None
            }
        productos_precios[producto_nombre]['precios'].append(precio)

    # Caclula las estadísticas de precios para cada producto
    for producto_data in productos_precios.values():
        precios = producto_data['precios']
        if precios:
            producto_data['precio_actual'] = precios[0].precio_unitario  # Most recent
            producto_data['precio_promedio'] = (
                sum(p.precio_unitario for p in precios) / len(precios))

            if len(precios) >= 2:
                producto_data['precio_anterior'] = precios[1].precio_unitario
                producto_data['variacion'] = (
                    producto_data['precio_actual'] - producto_data['precio_anterior'])
                if producto_data['precio_anterior'] > 0:
                    producto_data['porcentaje_variacion'] = (
                        (producto_data['variacion'] / producto_data['precio_anterior']) * 100)

    # Calula estadísticas generales del historial
    if historial.exists():
        precio_promedio_general = historial.aggregate(
            avg_precio=models.Avg('precio_unitario'))['avg_precio']
        productos_suministrados = historial.values('producto').distinct().count()
        precio_minimo = historial.aggregate(min_precio=models.Min('precio_unitario'))['min_precio']
        precio_maximo = historial.aggregate(max_precio=models.Max('precio_unitario'))['max_precio']
    else:
        precio_promedio_general = productos_suministrados = precio_minimo = precio_maximo = 0

    stats = {
        'precio_promedio_general': precio_promedio_general,
        'productos_suministrados': productos_suministrados,
        'total_transacciones': historial.count(),
        'precio_minimo': precio_minimo,
        'precio_maximo': precio_maximo,
    }

    return render(request, 'precios/historial_proveedor.html', {
        'proveedor': proveedor,
        'productos_precios': productos_precios,
        'historial': historial,
        'stats': stats,
    })

def comparar_precios_proveedores(request):
    """Vista para comparar precios entre proveedores."""
    producto_id = request.GET.get('producto')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if producto_id:
        producto = get_object_or_404(Producto, id=int(producto_id))

        # Toma el historial de precios del producto
        # pylint: disable=no-member
        historial_query = (
            HistorialPrecio.objects.filter(producto=producto).select_related(
                'proveedor', 'usuario'))

        # Aplicar filtros de fecha si se proporcionan
        if fecha_desde:
            historial_query = historial_query.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            fecha_hasta_dt = datetime.datetime.strptime(fecha_hasta, '%Y-%m-%d')
            fecha_hasta_dt = datetime.datetime.combine(fecha_hasta_dt.date(), datetime.time.max)
            historial_query = historial_query.filter(fecha__lte=fecha_hasta_dt)

        # Toma los últimos precios por proveedor
        precios_proveedores = []
        proveedores = Proveedor.objects.filter(activo=True)

        for proveedor in proveedores:
            ultimo_precio = historial_query.filter(proveedor=proveedor).first()

            if ultimo_precio:
                # Calcula el precio promedio del proveedor
                precios_proveedor = historial_query.filter(proveedor=proveedor)
                precio_promedio = precios_proveedor.aggregate(
                    avg=models.Avg('precio_unitario'))['avg']

                precios_proveedores.append({
                    'proveedor': proveedor,
                    'precio_actual': ultimo_precio.precio_unitario,
                    'precio_promedio': precio_promedio,
                    'fecha': ultimo_precio.fecha,
                    'usuario': ultimo_precio.usuario,
                    'compra': ultimo_precio.compra,
                    'total_registros': precios_proveedor.count()
                })

        # Ordena los precios por precio actual
        precios_proveedores.sort(key=lambda x: x['precio_actual'])

        # Calcula estadísticas de comparación
        if precios_proveedores:
            precios_actuales = [p['precio_actual'] for p in precios_proveedores]
            precio_menor = min(precios_actuales)
            precio_mayor = max(precios_actuales)
            precio_promedio_mercado = sum(precios_actuales) / len(precios_actuales)

            # Calcula diferencias y marca el mejor precio
            for precio_data in precios_proveedores:
                precio_data['ahorro_vs_menor'] = precio_data['precio_actual'] - precio_menor
                precio_data['es_mejor_precio'] = precio_data['precio_actual'] == precio_menor
                precio_data['diferencia_promedio'] = (
                    precio_data['precio_actual'] - precio_promedio_mercado)
        else:
            precio_menor = precio_mayor = precio_promedio_mercado = 0

        comparison_stats = {
            'precio_menor': precio_menor,
            'precio_mayor': precio_mayor,
            'precio_promedio_mercado': precio_promedio_mercado,
            'diferencia_extremos': precio_mayor - precio_menor,
            'porcentaje_diferencia': (
                ((precio_mayor - precio_menor) / precio_menor * 100)
                if precio_menor > 0 else 0)
        }
        context = {
            'producto': producto,
            'precios_proveedores': precios_proveedores,
            'productos': Producto.objects.all(),
            'comparison_stats': comparison_stats,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    else:
        context = {
            # pylint: disable=no-member
            'productos': Producto.objects.all() 
        }

    return render(request, 'precios/comparar_proveedores.html', context)

@login_required
def registrar_precio_manual(request):
    """Vista para registrar precios manualmente sin compra."""
    if request.method == 'POST':
        form = RegistroPrecioManualForm(request.POST)
        if form.is_valid():
            precio = form.save(commit=False)
            precio.usuario = request.user
            precio.save()
            messages.success(
                request, f'Precio registrado exitosamente para {precio.producto.nombre}')
            return redirect('/inventario/precios/')
    else:
        form = RegistroPrecioManualForm()

    return render(request, 'precios/registrar_precio.html', {'form': form})

def exportar_precios_csv(request): # pylint: disable=unused-argument
    """Export price history to CSV."""
    # pylint: disable=no-member
    try:
        historial = HistorialPrecio.objects.select_related('producto', 'proveedor', 'usuario').all()
        ahora = datetime.datetime.now()
        fecha_str = ahora.strftime('%Y-%m-%d_%H-%M')
        nombre_archivo = f'historial_precios_{fecha_str}.csv'
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}"'
        # Añade BOM para compatibilidad con Excel
        response.write('\ufeff')

        writer = csv.writer(response)
        writer.writerow([
            'Producto', 'Precio Unitario', 'Proveedor', 'Fecha', 'Usuario', 
            'Precio Anterior', 'Variación', '% Variación', 'Observaciones'
        ])

        for precio in historial:
            writer.writerow([
                precio.producto.nombre,
                precio.precio_unitario,
                precio.proveedor.nombre if precio.proveedor else 'Sin proveedor',
                precio.fecha.strftime('%d/%m/%Y %H:%M'),
                precio.usuario.username if precio.usuario else 'Sistema',
                precio.precio_anterior or 'N/A',
                precio.variacion_precio or 'N/A',
                f'{precio.porcentaje_variacion:.2f}%' if precio.porcentaje_variacion else 'N/A',
                precio.observaciones
            ])

        return response
    except Exception as e: # pylint: disable=broad-except
        return HttpResponse(f"Error al generar el CSV: {str(e)}", status=500)

def reporte_precios_pdf(request): # pylint: disable=unused-argument
    """Generate PDF report of price history."""
    # pylint: disable=no-member
    try:
        historial = HistorialPrecio.objects.select_related(
            'producto', 'proveedor', 'usuario').all()[:100]
        ahora = datetime.datetime.now()
        fecha_str = ahora.strftime('%Y-%m-%d_%H-%M')

        # Calculo de estadísticas
        stats = {
            'total_registros': historial.count(),
            'productos_unicos': historial.values('producto').distinct().count(),
            'proveedores_unicos': historial.values('proveedor').distinct().count(),
            'precio_promedio': historial.aggregate(
                avg_precio=models.Avg('precio_unitario'))['avg_precio'] or 0,
        }

        template = get_template('precios/reporte_precios_pdf.html')
        html = template.render({
            'historial': historial,
            'stats': stats,
            'fecha_generacion': ahora
        })

        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html.encode('UTF-8')), dest=buffer, encoding='UTF-8')

        if pisa_status.err:
            return HttpResponse("Error al generar PDF", status=500)

        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_precios_{fecha_str}.pdf"'
        return response

    except Exception as e: # pylint: disable=broad-except
        return HttpResponse(f"Error al generar el PDF: {str(e)}", status=500)

# Dashboard y edición

@login_required
def dashboard_inventario(request):
    """Vista del dashboard de inventario con estadísticas y gráficos."""
    # pylint: disable=no-member
    total_productos = Producto.objects.count()
    productos_sin_stock = Producto.objects.filter(stock_actual=0).count()
    productos_bajo_minimo = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).count()
    movimientos = MovimientoInventario.objects.values('tipo').annotate(
        total=Count('id')).order_by('tipo')
    tipos = [m['tipo'].capitalize() for m in movimientos]
    cantidades = [m['total'] for m in movimientos]
    colores_contexto = {
        'Entrada': 'rgba(75, 192, 192, 0.6)',
        'Salida': 'rgba(255, 99, 132, 0.6)',
        'Ajuste': 'rgba(255, 206, 86, 0.6)',
        'Devolucion': 'rgba(54, 162, 235, 0.6)',
    }
    colores_barras = (
        [colores_contexto.get(tipo.capitalize(), 'rgba(153, 102, 255, 0.6)') for tipo in tipos])
    alertas_stock_pendientes = (
        AlertaStock.objects.filter(atendido=False).select_related(
            'producto').order_by('-fecha_alerta'))
    proveedores = Producto.objects.values(
        'proveedor__nombre').annotate(total=Count('id')).order_by('-total')
    nombres_proveedores = [p['proveedor__nombre'] or 'Sin proveedor' for p in proveedores]
    cantidades_proveedor = [p['total'] for p in proveedores]
    context = {
        'total_productos': total_productos,
        'productos_sin_stock': productos_sin_stock,
        'productos_bajo_minimo': productos_bajo_minimo,
        'tipos_movimiento': tipos,
        'cantidades_movimiento': cantidades,
        'colores_barras': colores_barras,
        'alertas_stock': alertas_stock_pendientes,
        'nombres_proveedores': nombres_proveedores,
        'cantidades_proveedor': cantidades_proveedor,
    }
    return render(request, 'inventario/dashboard.html', context)

@login_required
def detalle_producto_lotes(request, producto_id):
    """Vista para mostrar los lotes de un producto específico."""
    # pylint: disable=no-member
    producto = get_object_or_404(Producto, id=producto_id)
    lotes = LoteProducto.objects.filter(
        producto=producto, activo=True).order_by('fecha_vencimiento')
    # Añade calculo de días hasta vencimiento y vencidos
    for lote in lotes:
        if lote.dias_hasta_vencimiento < 0:
            lote.dias_vencido = abs(lote.dias_hasta_vencimiento)
        else:
            lote.dias_vencido = 0
    # Aplica filtros si se envían parámetros
    form = LoteFiltroForm(request.GET or None)
    if form.is_valid():
        estado = form.cleaned_data.get('estado')
        if estado == 'vencido':
            lotes = lotes.filter(fecha_vencimiento__lt=timezone.now().date())
        elif estado == 'por_vencer':
            fecha_limite = timezone.now().date() + datetime.timedelta(days=30)
            lotes = lotes.filter(
                fecha_vencimiento__lte=fecha_limite,
                fecha_vencimiento__gte=timezone.now().date())
        elif estado == 'activo':
            lotes = lotes.filter(fecha_vencimiento__gte=timezone.now().date())

        if form.cleaned_data.get('fecha_vencimiento_desde'):
            lotes = lotes.filter(
                fecha_vencimiento__gte=form.cleaned_data['fecha_vencimiento_desde'])
        if form.cleaned_data.get('fecha_vencimiento_hasta'):
            lotes = lotes.filter(
                fecha_vencimiento__lte=form.cleaned_data['fecha_vencimiento_hasta'])

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
            # Crear historial de lote
            # pylint: disable=no-member
            HistorialLote.objects.create(
                lote=lote,
                tipo_cambio='creacion',
                cantidad_anterior=0,
                cantidad_nueva=lote.cantidad_inicial,
                usuario=request.user,  # Add the current user
                observaciones=(
                    f'Lote creado con {lote.cantidad_inicial} unidades por {request.user.username}')
            )
            # Actualizar stock del producto
            messages.success(request, f'Lote {lote.numero_lote} creado exitosamente.')
            return redirect('inventario:detalle_producto_lotes', producto_id=producto.id)
    else:
        form = LoteProductoForm(producto=producto)
    return render(request, 'productos/formulario_lote.html', {
        'form': form,
        'producto': producto,
        'action': 'Crear'
    })

def editar_lote(request, lote_id):
    """Vista para editar un lote existente."""
    lote = get_object_or_404(LoteProducto, id=lote_id)
    producto = lote.producto

    if request.method == 'POST':
        # pylint: disable=no-member
        form = LoteProductoForm(request.POST, instance=lote)
        if form.is_valid():
            # Guardar el lote modificado sin commit
            lote_modificado = form.save(commit=False)
            # Calula la diferencia de cantidad
            cantidad_anterior = lote.cantidad_actual
            cantidad_nueva = form.cleaned_data['cantidad_inicial']
            diferencia = cantidad_nueva - cantidad_anterior
            # Actualiza los campos del lote
            lote_modificado.cantidad_actual = cantidad_nueva
            lote_modificado.save()
            # Crear historial de lote
            HistorialLote.objects.create(
                lote=lote_modificado,
                tipo_cambio='modificacion',
                cantidad_anterior=cantidad_anterior,
                cantidad_nueva=cantidad_nueva,
                usuario=request.user,
                observaciones=f"Modificación manual: {form.cleaned_data.get('observaciones', '')}"
            )
            # Actualizar stock del producto si hay diferencia
            if diferencia != 0:
                producto = lote_modificado.producto
                producto.stock_actual += diferencia
                producto.save()

                # Crear movimiento de inventario
                # pylint: disable=no-member
                MovimientoInventario.objects.create(
                    producto=producto,
                    tipo_movimiento='ajuste',
                    cantidad=abs(diferencia),
                    direccion='entrada' if diferencia > 0 else 'salida',
                    usuario=request.user,
                    observaciones=(
                        f"Ajuste por modificación del lote #{lote_modificado.numero_lote}"),
                    lote=lote_modificado
                )
            messages.success(
                request, f"Lote #{lote_modificado.numero_lote} actualizado exitosamente.")
            return redirect(
                'inventario:detalle_producto_lotes', producto_id=lote_modificado.producto.id)
    else:
        form = LoteProductoForm(instance=lote)
    # Si el lote tiene una fecha de vencimiento, la formatea
    return render(request, 'productos/formulario_lote.html', {
        'form': form,
        'producto': producto,
        'lote': lote,
        'action': 'Editar'
    })

def historial_lotes(request, lote_id=None):
    """Vista para mostrar el historial de cambios de un lote o todos los lotes."""
    # pylint: disable=no-member
    if lote_id:
        lote = get_object_or_404(LoteProducto, id=lote_id)
        # Change 'fecha' to 'fecha_cambio' here:
        historial = HistorialLote.objects.filter(lote=lote).order_by('-fecha_cambio')
        titulo = f"Historial del Lote #{lote.numero_lote}"
    else:
        lote = None
        # Also update here if you have this line:
        historial = HistorialLote.objects.all().order_by('-fecha_cambio')
        titulo = "Historial de Todos los Lotes"

    return render(request, 'productos/historial_lotes.html', {
        'historial': historial,
        'lote': lote,
        'titulo': titulo
    })

def api_producto_lotes(request, producto_id): # pylint: disable=unused-argument
    """API para obtener los lotes de un producto específico."""
    # pylint: disable=no-member
    producto = get_object_or_404(Producto, id=producto_id)
    lotes = LoteProducto.objects.filter(producto=producto, activo=True).values(
        'id', 'numero_lote', 'fecha_vencimiento', 'cantidad_actual'
    )
    return JsonResponse(list(lotes), safe=False)

def toggle_block_product(request, producto_id):
    """Varia el estado de bloqueo de un producto."""
    # pylint: disable=no-member
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

    messages.success(request, mensaje)
    return redirect('/inventario/productos/')

def historial_bloqueos(request):
    """View audit history of product blocks."""
    # pylint: disable=no-member
    auditorias = AuditoriaInventario.objects.select_related(
        'producto', 'usuario_auditor').order_by('-fecha_inicio')

    # Paginación
    paginator = Paginator(auditorias, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'productos/historial_bloqueos.html', {
        'page_obj': page_obj,
        'auditorias': auditorias
    })
@login_required
def api_lotes_producto(request, producto_id): # pylint: disable=unused-argument
    """API para obtener los lotes disponibles de un producto."""
    # pylint: disable=no-member
    try:
        producto = Producto.objects.get(id=producto_id)
        # Filtra los lotes activos y no vencidos
        lotes = LoteProducto.objects.filter(
            producto=producto,
            cantidad_actual__gt=0
        ).exclude(
            fecha_vencimiento__lt=timezone.now().date()
        ).values('id', 'numero_lote', 'fecha_vencimiento', 'cantidad_actual')

        return JsonResponse(list(lotes), safe=False)
    except Producto.DoesNotExist:
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)

# Proyectos
@login_required
def listar_proyectos(request):
    """Vista para listar todos los proyectos."""
    # pylint: disable=no-member
    # Filtros
    estado = request.GET.get('estado')
    responsable = request.GET.get('responsable')
    buscar = request.GET.get('buscar')
    # Filtra los proyectos según los parámetros
    proyectos = Proyecto.objects.all()
    if estado:
        proyectos = proyectos.filter(estado=estado)
    if responsable:
        proyectos = proyectos.filter(responsable_id=responsable)
    if buscar:
        proyectos = proyectos.filter(Q(nombre__icontains=buscar) | Q(descripcion__icontains=buscar))

    # Estadísticas
    stats = {
        # pylint: disable=no-member
        'total': Proyecto.objects.count(),
        'en_ejecucion': Proyecto.objects.filter(estado='ejecucion').count(),
        'completados': Proyecto.objects.filter(estado='completado').count(),
        'planificacion': Proyecto.objects.filter(estado='planificacion').count(),
    }

    # Datos para filtros
    responsables = get_user_model().objects.filter(proyectos_responsable__isnull=False).distinct()

    return render(request, 'proyectos/listar_proyecto.html', {
        'proyectos': proyectos,
        'stats': stats,
        'responsables': responsables,
        'estado_seleccionado': estado,
        'responsable_seleccionado': responsable,
        'busqueda': buscar,
    })

@login_required
def crear_proyecto(request):
    """Vista para crear un nuevo proyecto."""
    if request.method == 'POST':
        form = ProyectoForm(request.POST)
        if form.is_valid():
            proyecto = form.save(commit=False)
            proyecto.creado_por = request.user
            proyecto.save()
            messages.success(request, f'Proyecto "{proyecto.nombre}" creado exitosamente.')
            return redirect('inventario:listar_proyectos')
    else:
        form = ProyectoForm()
    # Renderiza el formulario de creación de proyecto
    return render(request, 'proyectos/formulario_proyecto.html', {
        'form': form,
        'action': 'Crear'
    })

@login_required
def editar_proyecto(request, proyecto_id):
    """Vista para editar un proyecto existente."""
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == 'POST':
        form = ProyectoForm(request.POST, instance=proyecto)
        if form.is_valid():
            form.save()
            messages.success(request, f'Proyecto "{proyecto.nombre}" actualizado exitosamente.')
            return redirect('inventario:detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ProyectoForm(instance=proyecto)

    return render(request, 'proyectos/formulario_proyecto.html', {
        'form': form,
        'proyecto': proyecto,
        'action': 'Editar'
    })

@login_required
def detalle_proyecto(request, proyecto_id):
    """Vista para ver los detalles de un proyecto y sus materiales."""
    # pylint: disable=no-member
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    materiales = MaterialProyecto.objects.filter(
        proyecto=proyecto).select_related('producto', 'lote')
    # Calcular estadísticas de materiales
    stats = {
        'total_materiales': materiales.count(),
        'costo_total': sum(material.costo_total for material in materiales),
        'productos_unicos': materiales.values('producto').distinct().count(),
    }

    return render(request, 'proyectos/detalle_proyecto.html', {
        'proyecto': proyecto,
        'materiales': materiales,
        'stats': stats,
    })

@login_required
def asignar_material(request, proyecto_id):
    """Vista para asignar un material a un proyecto."""
    # pylint: disable=no-member
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)
    if request.method == 'POST':
        form = MaterialProyectoForm(request.POST, proyecto=proyecto)
        if form.is_valid():
            material = form.save(commit=False)
            material.proyecto = proyecto
            # Verificar stock disponible
            producto = material.producto
            cantidad_requerida = material.cantidad_asignada
            # Check if product is blocked using AuditoriaInventario
            auditoria_activa = AuditoriaInventario.objects.filter(
                producto=producto, bloqueado=True
            ).exists()
            if auditoria_activa:
                form.add_error('producto',
                    'Este producto está bloqueado por auditoría y no ' \
                    'puede ser asignado a proyectos.')
                return render(request, 'proyectos/formulario_material.html', {
                    'form': form,
                    'proyecto': proyecto,
                    'action': 'Asignar'
                })

            if cantidad_requerida > producto.stock_actual:
                form.add_error('cantidad_asignada',
                              f'No hay suficiente stock. Disponible: {producto.stock_actual}')
            else:
                # Si se seleccionó un lote, actualizar su cantidad
                if material.lote:
                    lote = material.lote
                    if cantidad_requerida > lote.cantidad_actual:
                        form.add_error(
                            'lote',
                            (
                            f'No hay suficiente cantidad en este lote. '
                            f'Disponible: {lote.cantidad_actual}'
                            )
                        )
                        return render(request, 'proyectos/formulario_material.html', {
                            'form': form,
                            'proyecto': proyecto,
                            'action': 'Asignar'
                        })

                    # Registrar en historial del lote
                    HistorialLote.objects.create(
                        lote=lote,
                        tipo_cambio='uso',
                        cantidad_anterior=lote.cantidad_actual,
                        cantidad_nueva=lote.cantidad_actual - cantidad_requerida,
                        usuario=request.user,
                        observaciones=f"Asignado al proyecto: {proyecto.nombre}"
                    )

                # Registrar movimiento de inventario
                MovimientoInventario.objects.create(
                    producto=producto,
                    cantidad=cantidad_requerida,
                    tipo='salida',
                    usuario=request.user,
                    observaciones=f"Asignado al proyecto: {proyecto.nombre}",
                    lote=material.lote
                )
                # Guardar el material asignado
                material.save()

                messages.success(
                    request,
                    (
                        f'{cantidad_requerida} unidades de '
                        f'{producto.nombre} asignadas al proyecto.')
                    )
                return redirect('inventario:detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = MaterialProyectoForm(proyecto=proyecto)

    return render(request, 'proyectos/formulario_material.html', {
        'form': form,
        'proyecto': proyecto,
        'action': 'Asignar'
    })

@login_required
def actualizar_uso_material(request, material_id):
    """Vista para actualizar la cantidad utilizada de un material."""
    material = get_object_or_404(MaterialProyecto, id=material_id)
    proyecto = material.proyecto
    if request.method == 'POST':
        form = ActualizarUsoMaterialForm(request.POST, instance=material)
        if form.is_valid():
            cantidad_anterior = material.cantidad_utilizada
            material = form.save()
            # Verificar si la cantidad utilizada cambió
            if material.cantidad_utilizada != cantidad_anterior:
                diferencia = material.cantidad_utilizada - cantidad_anterior
                # Registrar en el historial si la diferencia es significativa
                if diferencia != 0:
                    messages.success(
                        request,
                        (
                        f'Uso de {material.producto.nombre} actualizado: '
                        f'{material.cantidad_utilizada} unidades utilizadas.'
                    )
                    )
            else:
                messages.info(request, 'No se detectaron cambios en la cantidad utilizada.')

            return redirect('inventario:detalle_proyecto', proyecto_id=proyecto.id)
    else:
        form = ActualizarUsoMaterialForm(instance=material)

    return render(request, 'proyectos/formulario_uso_material.html', {
        'form': form,
        'material': material,
        'proyecto': proyecto
    })

@login_required
def eliminar_material(request, material_id):
    """Vista para eliminar un material asignado a un proyecto."""
    # pylint: disable=no-member
    material = get_object_or_404(MaterialProyecto, id=material_id)
    proyecto = material.proyecto
    producto = material.producto
    lote = material.lote
    cantidad_asignada = material.cantidad_asignada
    cantidad_utilizada = material.cantidad_utilizada
    if request.method == 'POST':
        try:
            # Calcula la cantidad a devolver al inventario
            cantidad_devolver = cantidad_asignada - cantidad_utilizada
            # Log para debugging
            print(
                f'DEBUG: Material deletion - Assigned: {cantidad_asignada}, Used: '
                f'{cantidad_utilizada}, To Return: {cantidad_devolver}')
            if cantidad_devolver > 0:
                if lote:
                    # Registrar en el historial del lote
                    HistorialLote.objects.create(
                        lote=lote,
                        tipo_cambio='devolucion',
                        cantidad_anterior=lote.cantidad_actual,
                        cantidad_nueva=
                        (
                            lote.cantidad_actual + cantidad_devolver
                        ),
                        usuario=request.user,
                        observaciones=f"Devuelto del proyecto: {proyecto.nombre}"
                    )

                # Registrar el movimiento de inventario
                MovimientoInventario.objects.create(
                    producto=producto,
                    cantidad=cantidad_devolver,
                    tipo='entrada',
                    usuario=request.user,
                    observaciones=f"Devuelto del proyecto: {proyecto.nombre}",
                    lote=lote
                )

                print("DEBUG: Created inventory movement record")

            # Borra el material del proyecto
            material.delete()
            print("DEBUG: Material deleted from project")

            messages.success(
                request,
                (
                    f'Material {producto.nombre} eliminado del proyecto. Se han devuelto '
                    f'{cantidad_devolver} unidades al inventario.'
                )
            )

        except Exception as e: # pylint: disable=broad-except
            # Imprime el error en la consola para debugging
            print(f"ERROR in eliminar_material: {str(e)}")
            messages.error(request, f"Error al eliminar el material: {str(e)}")

        return redirect('inventario:detalle_proyecto', proyecto_id=proyecto.id)

    return render(request, 'proyectos/confirmar_eliminar_material.html', {
        'material': material,
        'proyecto': proyecto
    })

@login_required
def api_producto_info(request, producto_id): # pylint: disable=unused-argument
    """API para obtener información de un producto, incluido stock y lotes disponibles."""
    # pylint: disable=no-member
    try:
        producto = Producto.objects.get(id=producto_id)
        # Revisa si el producto está bloqueado
        is_blocked = AuditoriaInventario.objects.filter(
            producto=producto, bloqueado=True
        ).exists()

        if is_blocked:
            return JsonResponse({
                'error': 'Este producto está bloqueado y no puede ser asignado a proyectos.'
            }, status=400)

        # Toma los lotes activos y con stock disponible
        lotes = LoteProducto.objects.filter(
            producto=producto,
            cantidad_actual__gt=0
        ).values('id', 'numero_lote', 'fecha_vencimiento', 'cantidad_actual')

        # Prepara la respuesta JSON
        data = {
            'id': producto.id,
            'nombre': producto.nombre,
            'stock_actual': producto.stock_actual,
            'lotes': list(lotes)
        }

        # Formatea las fechas de vencimiento de los lotes
        for lote in data['lotes']:
            if 'fecha_vencimiento' in lote and lote['fecha_vencimiento']:
                lote['fecha_vencimiento'] = lote['fecha_vencimiento'].strftime('%Y-%m-%d')

        return JsonResponse(data)

    except Producto.DoesNotExist: # pylint: disable=no-member
        return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    except Exception as e: # pylint: disable=broad-except
        # Añade un log para el error
        return JsonResponse({
            'error': f'Error al obtener información del producto: {str(e)}'},
            status=500)

def configuracion_sistema(request):
    """Vista para mostrar y actualizar las configuraciones generales del sistema."""
    if request.method == 'POST':
        form = ConfiguracionSistemaForm(request.POST)
        if form.is_valid():
            form.guardar()
            messages.success(request, 'Configuración actualizada correctamente.')
            return redirect('inventario:configuracion_sistema')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ConfiguracionSistemaForm()

    return render(request, 'configuracion/configuracion.html', {'form': form})

@login_required
def informe_inventario(request):
    """Vista para generar un informe de inventario con filtros y gráficos."""
    # pylint: disable=no-member
    form = InformeInventarioFiltroForm(request.GET or None)
    productos = Producto.objects.all()

    if form.is_valid():
        ubicacion = form.cleaned_data.get('ubicacion')
        categoria = form.cleaned_data.get('categoria')
        proveedor = form.cleaned_data.get('proveedor')
        stock_min = form.cleaned_data.get('stock_min')
        stock_max = form.cleaned_data.get('stock_max')
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')

        if ubicacion:
            productos = productos.filter(ubicacion=ubicacion)
        if categoria:
            productos = productos.filter(categoria=categoria)
        if proveedor:
            productos = productos.filter(proveedor__nombre=proveedor)
        if stock_min is not None:
            productos = productos.filter(stock_actual__gte=stock_min)
        if stock_max is not None:
            productos = productos.filter(stock_actual__lte=stock_max)
        if fecha_inicio:
            productos = productos.filter(fecha_ingreso__date__gte=fecha_inicio)
        if fecha_fin:
            productos = productos.filter(fecha_ingreso__date__lte=fecha_fin)

    datos_categoria = productos.values(
        'categoria').annotate(total=Count('id')).order_by(
            'categoria')
    labels = [dato['categoria'] or 'Sin categoría' for dato in datos_categoria]
    valores = [dato['total'] for dato in datos_categoria]

    export = request.GET.get('export')
    if export == 'pdf':
        AuditoriaInformeInventario.objects.create(
            usuario=request.user,
            tipo_exportacion='PDF',
            filtros_aplicados=request.GET.urlencode(),
            total_registros=productos.count()
        )
        return exportar_pdf_inventario(productos, request)
    elif export == 'excel':
        AuditoriaInformeInventario.objects.create(
            usuario=request.user,
            tipo_exportacion='Excel',
            filtros_aplicados=request.GET.urlencode(),
            total_registros=productos.count()
        )
        return exportar_excel_inventario(productos)

    contexto = {
        'form': form,
        'productos_filtrados': productos,
        'datos_categoria': list(datos_categoria),
        'labels': labels,
        'valores': valores,
    }
    return render(request, 'reportes/informe_inventario.html', contexto)

def lista_ordenes_compra(request):
    """Vista para listar órdenes de compra con filtros."""
    form = OrdenCompraFiltroForm(request.GET or None)
    ordenes_qs = OrdenCompra.objects.all().order_by('-fecha_creacion')
    ordenes = ordenes_qs  # por defecto

    if form.is_valid():
        if form.cleaned_data.get('fecha_inicio'):
            fecha_inicio = form.cleaned_data['fecha_inicio']
            ordenes_qs = ordenes_qs.filter(
                fecha_creacion__gte=datetime.datetime.combine(fecha_inicio, datetime.time.min))
        if form.cleaned_data.get('fecha_fin'):
            fecha_fin = form.cleaned_data['fecha_fin']
            ordenes_qs = ordenes_qs.filter(
                fecha_creacion__lte=datetime.datetime.combine(fecha_fin, datetime.time.max))
        if form.cleaned_data.get('estado'):
            ordenes_qs = ordenes_qs.filter(estado=form.cleaned_data['estado'])
        if form.cleaned_data.get('proveedor'):
            ordenes_qs = ordenes_qs.filter(proveedor=form.cleaned_data['proveedor'])

    # Paginación
    paginator = Paginator(ordenes_qs, 10)
    page_number = request.GET.get('page')
    try:
        ordenes = paginator.page(page_number)
    except PageNotAnInteger:
        ordenes = paginator.page(1)
    except EmptyPage:
        ordenes = paginator.page(paginator.num_pages)

    # Excluir 'page' del querystring para mantener filtros
    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()

    return render(request, 'compras/lista_ordenes_compra.html', {
        'ordenes': ordenes,
        'filtro_form': form,
        'querystring': querystring
    })

def detalle_orden_compra(request, orden_id):
    orden = get_object_or_404(OrdenCompra, id=orden_id)
    return render(request, 'compras/detalle_orden_compra.html', {'orden': orden})

@login_required
@user_passes_test(is_staff)
def aprobar_orden_compra(request, orden_id):
    """Aprobar una orden de compra."""
    orden = get_object_or_404(OrdenCompra, id=orden_id)
    if orden.estado == 'sugerida':
        orden.estado = 'aprobada'
        orden.fecha_aprobacion = timezone.now()
        orden.usuario_aprobacion = request.user
        orden.save()
        
        # Crear registro en el log
        OrdenCompraLog.objects.create(
            orden=orden,
            estado='aprobada',
            descripcion=f"Orden aprobada por {request.user.username}",
            usuario=request.user
        )
        
        messages.success(request, "Orden aprobada exitosamente.")
    else:
        messages.warning(request, "Solo se pueden aprobar órdenes en estado 'sugerida'.")
    return redirect('inventario:detalle_orden_compra', orden_id=orden.id)

@login_required
@user_passes_test(is_staff)
def cancelar_orden_compra(request, orden_id):
    """Cancelar una orden de compra."""
    orden = get_object_or_404(OrdenCompra, id=orden_id)
    if orden.estado in ['sugerida', 'pendiente', 'aprobada']:
        orden.estado = 'cancelada'
        orden.fecha_cancelacion = timezone.now()
        orden.save()
        
        # Crear registro en el log
        OrdenCompraLog.objects.create(
            orden=orden,
            estado='cancelada',
            descripcion=f"Orden cancelada por {request.user.username}",
            usuario=request.user
        )
        
        messages.warning(request, "Orden cancelada.")
    else:
        messages.warning(request, "Solo se pueden cancelar órdenes que no estén recepcionadas o ya canceladas.")
    return redirect('inventario:detalle_orden_compra', orden_id=orden.id)

@login_required
@user_passes_test(is_staff)
def recibir_orden_compra(request, orden_id):
    """Recibir una orden de compra y generar lotes."""
    orden = get_object_or_404(OrdenCompra, id=orden_id)

    if orden.estado != 'aprobada':
        messages.warning(request, "Solo se pueden recibir órdenes en estado 'aprobada'.")
        return redirect('inventario:detalle_orden_compra', orden_id=orden.id)

    try:
        orden.estado = 'recepcionada'
        orden.fecha_recepcion = timezone.now()
        orden.save()

        lotes_creados = []

        for item in orden.items.all():
            producto = item.producto
            lote = LoteProducto.objects.create(
                producto=producto,
                cantidad_inicial=item.cantidad,
                cantidad_actual=item.cantidad,
                numero_lote=f"OC{orden.id}-P{producto.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                fecha_vencimiento=timezone.now().date() + datetime.timedelta(days=30),  # Por defecto, vence en 30 días
            )
            producto.stock_actual += item.cantidad
            producto.save()
            
            # Marcar alertas como atendidas si ya se resolvió el bajo stock
            from .models import AlertaStock
            if producto.stock_actual >= producto.stock_minimo:
                AlertaStock.objects.filter(producto=producto, atendido=False).update(atendido=True)
                
            lotes_creados.append(lote.id)

        # Crear registro en el log
        OrdenCompraLog.objects.create(
            orden=orden,
            estado='recepcionada',
            descripcion=f"Orden recepcionada por {request.user.username}. {len(lotes_creados)} lotes generados.",
            usuario=request.user
        )

        if lotes_creados:
            messages.success(request, f"Orden recepcionada. {len(lotes_creados)} lotes generados satisfactoriamente.")
        else:
            messages.success(request, "Orden recepcionada.")

    except Exception as e:
        messages.error(request, f"Error al recibir la orden: {str(e)}")
        logger.error(f"Error receiving order {orden_id}: {str(e)}")

    return redirect('inventario:detalle_orden_compra', orden_id=orden.id)

@login_required
@user_passes_test(is_staff)
def editar_orden_compra(request, orden_id):
    """Vista para editar una orden de compra existente."""
    orden = get_object_or_404(OrdenCompra, id=orden_id)
    
    # Verificar que la orden se pueda editar
    if orden.estado not in ['sugerida', 'pendiente']:
        messages.error(request, "Solo se pueden editar órdenes en estado 'sugerida' o 'pendiente'.")
        return redirect('inventario:detalle_orden_compra', orden_id=orden.id)
    
    productos_disponibles = Producto.objects.filter(proveedor=orden.proveedor)

    if request.method == 'POST':
        try:
            productos_ids = request.POST.getlist('productos[]')
            cantidades = request.POST.getlist('cantidades[]')
            precios = request.POST.getlist('precios[]')
            
            # Validar que todos los arrays tengan la misma longitud
            if len(productos_ids) != len(cantidades) or len(productos_ids) != len(precios):
                messages.error(request, "Error en los datos del formulario. Por favor, inténtalo de nuevo.")
                return redirect('inventario:editar_orden_compra', orden_id=orden.id)
            
            productos_validos = []
            productos_agregados = set()

            # Procesar cada fila del formulario
            for i in range(len(productos_ids)):
                try:
                    producto_id = int(productos_ids[i])
                    cantidad = int(cantidades[i]) if cantidades[i] else 0
                    precio_unitario = float(precios[i]) if precios[i] else 0.0

                    # Validar datos
                    if cantidad <= 0:
                        continue

                    if producto_id in productos_agregados:
                        continue  # evitar productos duplicados

                    producto = Producto.objects.get(id=producto_id, proveedor=orden.proveedor)
                    productos_validos.append((producto, cantidad, precio_unitario))
                    productos_agregados.add(producto_id)

                except (ValueError, Producto.DoesNotExist, IndexError):
                    continue  # ignora cualquier fila mal formada

            if not productos_validos:
                messages.error(request, "Debe agregar al menos un producto válido con cantidad mayor a 0.")
                return redirect('inventario:editar_orden_compra', orden_id=orden.id)

            # Guardar estado anterior para el log
            items_anterior = list(orden.items.all().values('producto__nombre', 'cantidad', 'precio_unitario'))
            
            # Borrar todos los ítems existentes
            orden.items.all().delete()

            # Crear nuevos ítems
            for producto, cantidad, precio_unitario in productos_validos:
                ItemOrdenCompra.objects.create(
                    orden=orden,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario
                )

            # Crear registro en el log
            OrdenCompraLog.objects.create(
                orden=orden,
                estado='modificada',
                descripcion=f"Orden modificada por {request.user.username}. Productos actualizados.",
                usuario=request.user
            )

            messages.success(request, "Orden de compra actualizada correctamente.")
            return redirect('inventario:detalle_orden_compra', orden_id=orden.id)
            
        except Exception as e:
            messages.error(request, f"Error al actualizar la orden: {str(e)}")
            logger.error(f"Error editing order {orden_id}: {str(e)}")
            return redirect('inventario:editar_orden_compra', orden_id=orden.id)

    return render(request, 'Compras/formulario_orden_compra.html', {
        'orden': orden,
        'productos_disponibles': productos_disponibles
    })

@login_required
def obtener_productos_disponibles(request, proveedor_id):
    print("LLAMADA AJAX RECIBIDA")
    seleccionados = request.GET.getlist('seleccionados[]')
    productos = Producto.objects.filter(proveedor_id=proveedor_id).exclude(id__in=seleccionados)
    data = [{'id': p.id, 'nombre': p.nombre} for p in productos]
    return JsonResponse(data, safe=False)


@login_required
@user_passes_test(lambda u: u.is_staff)
def crear_orden_compra(request):
    """Crear una nueva orden de compra."""
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        proveedor_id = request.POST.get('proveedor')
        productos_ids = request.POST.getlist('productos[]')
        cantidades = request.POST.getlist('cantidades[]')
        precios = request.POST.getlist('precios[]')

        if not proveedor_id:
            messages.error(request, "Debe seleccionar un proveedor.")
            return redirect('inventario:crear_orden_compra')

        try:
            proveedor = Proveedor.objects.get(id=proveedor_id)
        except Proveedor.DoesNotExist:
            messages.error(request, "Proveedor inválido.")
            return redirect('inventario:crear_orden_compra')

        productos_validos = []

        for i in range(len(productos_ids)):
            if not productos_ids[i] or not cantidades[i] or not precios[i]:
                continue

            try:
                producto_id = int(productos_ids[i])
                cantidad = int(cantidades[i])
                precio_unitario = float(precios[i])

                if cantidad <= 0:
                    continue

                producto = Producto.objects.get(id=producto_id, proveedor=proveedor)
                productos_validos.append((producto, cantidad, precio_unitario))

            except (ValueError, Producto.DoesNotExist):
                continue

        if not productos_validos:
            messages.error(request, "Debe agregar al menos un producto con cantidad válida.")
            return redirect('inventario:crear_orden_compra')

        try:
            # Crear la orden de compra
            orden = OrdenCompra.objects.create(proveedor=proveedor)

            for producto, cantidad, precio_unitario in productos_validos:
                ItemOrdenCompra.objects.create(
                    orden=orden,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario
                )

            # Crear registro en el log
            OrdenCompraLog.objects.create(
                orden=orden,
                estado='creada',
                descripcion=f"Orden creada por {request.user.username} con {len(productos_validos)} productos",
                usuario=request.user
            )

            messages.success(request, f"Orden #{orden.id} creada exitosamente.")
            return redirect('inventario:detalle_orden_compra', orden_id=orden.id)
            
        except Exception as e:
            messages.error(request, f"Error al crear la orden: {str(e)}")
            logger.error(f"Error creating order: {str(e)}")
            return redirect('inventario:crear_orden_compra')

    return render(request, 'Compras/crear_orden_compra.html', {
        'orden': None,
        'proveedores': proveedores,
    })
@login_required
def productos_por_proveedor(request):
    proveedor_id = request.GET.get('proveedor_id')
    productos = Producto.objects.filter(proveedor_id=proveedor_id).values('id', 'nombre')
    return JsonResponse(list(productos), safe=False)