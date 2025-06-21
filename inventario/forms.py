"""
Formularios del módulo de inventario.
Este archivo contiene los formularios ModelForm utilizados para crear y editar
productos, movimientos de inventario, proveedores y kits de productos.
"""

from django.utils import timezone
from django import forms
from django.contrib.auth import get_user_model
from .models import (
    Producto, MovimientoInventario, Proveedor, KitProducto,
    CompraProveedor, EvaluacionProveedor, LoteProducto, HistorialPrecio,
    Proyecto, MaterialProyecto, AuditoriaInventario, ConfiguracionSistema
)

User = get_user_model()

class ProductoForm(forms.ModelForm):
    """Formulario para crear o actualizar un producto del inventario."""

    class Meta:
        """Especifica los campos y widgets del formulario."""
        model = Producto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Taladro eléctrico'}),
            'descripcion': 
                forms.Textarea(attrs={'placeholder': 'Especifica los detalles del producto'}),
            'ubicacion': forms.TextInput(attrs={'placeholder': 'Ej. Bodega A, estante 3'}),
            'categoria': forms.TextInput(attrs={'placeholder': 'Ej. Herramientas'}),
            'fecha_vencimiento':
                forms.DateInput(attrs={'placeholder': 'DD/MM/AAAA',
                                       'type': 'date',
                                       'class': 'form-control',
                                       'min': timezone.now().date().isoformat()}),
            'stock_actual': forms.NumberInput(attrs={'placeholder': 'Cantidad en inventario'}),
            'stock_minimo': forms.NumberInput(attrs={'placeholder': 'Cantidad mínima'}),
            'precio': forms.NumberInput(attrs={'placeholder': 'Ej. 19990'}),
            'numero_serie': forms.TextInput(attrs={'placeholder': 'Ej. SN123456789'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

        self.fields['fecha_vencimiento'].widget.attrs['min'] = timezone.now().date().isoformat()


class ProductoEditableForm(forms.ModelForm):
    """Formulario para editar un producto sin permitir cambios en ciertos campos."""

    class Meta:
        """Especifica los campos y widgets del formulario."""
        model = Producto
        fields = [
            'nombre', 'descripcion', 'numero_serie', 'ubicacion',
            'categoria', 'proveedor', 'fecha_vencimiento',
            'stock_actual', 'stock_minimo'
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_vencimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': timezone.now().date().isoformat()
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        campos_no_editables = ['nombre', 'numero_serie', 'categoria']
        for campo in campos_no_editables:
            self.fields[campo].disabled = True
            self.fields[campo].widget.attrs.update({
                'readonly': True,
                'class': 'form-control bg-secondary-subtle text-dark'
            })

        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')


class MovimientoInventarioForm(forms.ModelForm):
    """Formulario para crear movimientos de inventario."""

    class Meta:
        """Especifica los campos y widgets del formulario."""
        model = MovimientoInventario
        fields = ['producto', 'lote', 'tipo', 'cantidad', 'observaciones']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'lote': forms.Select(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Make lote field optional initially
        self.fields['lote'].required = False
        self.fields['lote'].empty_label = "Seleccionar lote (opcional)"

        # If a product is selected, filter lotes
        if 'producto' in self.data:
            try:
                producto_id = int(self.data.get('producto'))
                self.fields['lote'].queryset = LoteProducto.objects.filter(# pylint: disable=no-member
                    producto_id=producto_id,
                    activo=True
                ).order_by('fecha_vencimiento')
            except (ValueError, TypeError):
                self.fields['lote'].queryset = LoteProducto.objects.none()# pylint: disable=no-member
        elif self.instance.pk:
            self.fields['lote'].queryset = LoteProducto.objects.filter(# pylint: disable=no-member
                producto=self.instance.producto,
                activo=True
            ).order_by('fecha_vencimiento')
        else:
            self.fields['lote'].queryset = LoteProducto.objects.none()# pylint: disable=no-member

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        lote = cleaned_data.get('lote')
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')

        # Validate that lote belongs to the selected product
        if lote and producto and lote.producto != producto:
            raise forms.ValidationError(
                'El lote seleccionado no pertenece al producto seleccionado.')

        # Validate stock for salida movements
        if tipo == 'salida' and cantidad:
            if lote:
                if cantidad > lote.cantidad_actual:
                    raise forms.ValidationError(
                        f'No hay suficiente stock en el lote {lote.numero_lote}. '
                        f'Disponible: {lote.cantidad_actual}'
                    )
            elif producto:
                if cantidad > producto.stock_actual:
                    raise forms.ValidationError(
                        f'No hay suficiente stock del producto. '
                        f'Disponible: {producto.stock_actual}'
                    )
        return cleaned_data


class MovimientoFiltroForm(forms.Form):
    """Formulario para filtrar movimientos de inventario."""

    TIPO_CHOICES = [
        ('', 'Todos los tipos'),
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste', 'Ajuste'),
        ('devolucion', 'Devolución'),
    ]

    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    tipo_movimiento = forms.ChoiceField(
        choices=TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),# pylint: disable=no-member
        required=False,
        empty_label="Todos los productos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    usuario = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True).order_by('username'),
        required=False,
        empty_label="Todos los usuarios",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users who have created movements
        users_with_movements = User.objects.filter(
            movimientoinventario__isnull=False
        ).distinct().order_by('username')

        self.fields['usuario'].queryset = users_with_movements


class CompraProveedorForm(forms.ModelForm):
    """Formulario para registrar compras a proveedores."""

    class Meta:
        """Especifica los campos y widgets del formulario."""
        model = CompraProveedor
        fields = ['producto', 'cantidad', 'precio_unitario', 'numero_factura']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': 'Ejemplo: 15.990'}),
            'numero_factura': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EvaluacionProveedorForm(forms.ModelForm):
    """Formulario para registrar evaluaciones de proveedores."""

    class Meta:
        """"Especifica los campos y widgets del formulario."""
        model = EvaluacionProveedor
        fields = ['calificacion', 'comentario']
        widgets = {
            'calificacion': forms.Select(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ProveedorForm(forms.ModelForm):
    """Formulario para registrar o editar proveedores."""

    class Meta:
        """Especifica los campos y widgets del formulario."""
        model = Proveedor
        fields = '__all__'


class KitProductoForm(forms.ModelForm):
    """Formulario para crear kits de productos."""

    class Meta:
        """Especifica los campos y widgets del formulario."""
        model = KitProducto
        fields = '__all__'


class LoteProductoForm(forms.ModelForm):
    """Formulario para crear/editar lotes de productos."""

    class Meta:
        """"Especifica los campos y widgets del formulario."""
        model = LoteProducto
        fields = ['numero_lote', 'fecha_vencimiento', 'cantidad_inicial', 'observaciones']
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'numero_lote': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: LT-2025-001'}),
            'cantidad_inicial': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        lote = super().save(commit=False)
        if self.producto:
            lote.producto = self.producto
        lote.cantidad_actual = lote.cantidad_inicial
        if commit:
            lote.save()
            # Note: History record creation moved to view to capture user
        return lote


class LoteFiltroForm(forms.Form):
    """Formulario para filtrar lotes."""

    ESTADO_CHOICES = [
        ('', 'Todos'),
        ('activo', 'Activos'),
        ('vencido', 'Vencidos'),
        ('por_vencer', 'Por vencer (30 días)'),
    ]
    estado = forms.ChoiceField(
        choices=ESTADO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}))
    fecha_vencimiento_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'}))
    fecha_vencimiento_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'}))

class HistorialPrecioFiltroForm(forms.Form):
    """Formulario para filtrar el historial de precios."""

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),# pylint: disable=no-member
        required=False,
        empty_label="Todos los productos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.filter(activo=True),# pylint: disable=no-member
        required=False,
        empty_label="Todos los proveedores",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )


class RegistroPrecioManualForm(forms.ModelForm):
    """Formulario para registrar precios manualmente sin compra."""

    class Meta:
        """"Especifica los campos y widgets del formulario."""
        model = HistorialPrecio
        fields = ['producto', 'precio_unitario', 'proveedor', 'observaciones']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01', 
                'min': '0',
                'placeholder': 'Ejemplo: 15.990'
            }),
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['proveedor'].required = False
        self.fields['observaciones'].help_text = '' \
        'Motivo del registro de precio (ej: cotización, precio de mercado, etc.)'
        self.fields['observaciones'].required = True


class ProyectoForm(forms.ModelForm):
    """Formulario para crear y editar proyectos."""
    class Meta:
        """"Especifica los campos y widgets del formulario."""
        model = Proyecto
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin_estimada',
                  'responsable', 'estado', 'notas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin_estimada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'responsable': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class MaterialProyectoForm(forms.ModelForm):
    """Formulario para asignar materiales a proyectos."""

    class Meta:
        """"Especifica los campos y widgets del formulario."""
        model = MaterialProyecto
        fields = ['producto', 'cantidad_asignada', 'lote', 'notas']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_asignada': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'lote': forms.Select(attrs={'class': 'form-select'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        self.proyecto = kwargs.pop('proyecto', None)
        super().__init__(*args, **kwargs)

        # Get IDs of blocked products through AuditoriaInventario
        blocked_product_ids = AuditoriaInventario.objects.filter(# pylint: disable=no-member
            bloqueado=True
        ).values_list('producto_id', flat=True)

        # Filter products with stock available and not blocked
        self.fields['producto'].queryset = Producto.objects.filter(# pylint: disable=no-member
            stock_actual__gt=0
        ).exclude(
            id__in=blocked_product_ids
        )

        # Inicialmente deshabilitar el campo de lote
        self.fields['lote'].queryset = LoteProducto.objects.none()# pylint: disable=no-member
        self.fields['lote'].required = False

        # Si ya hay un producto seleccionado (por ejemplo, al editar)
        if 'producto' in self.data:
            try:
                producto_id = int(self.data.get('producto'))
                self.fields['lote'].queryset = LoteProducto.objects.filter(# pylint: disable=no-member
                    producto_id=producto_id,
                    cantidad_actual__gt=0
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.producto:
            self.fields['lote'].queryset = LoteProducto.objects.filter(# pylint: disable=no-member
                producto=self.instance.producto,
                cantidad_actual__gt=0
            )


class ActualizarUsoMaterialForm(forms.ModelForm):
    """Formulario para actualizar la cantidad utilizada de un material en un proyecto."""

    class Meta:
        """"Especifica los campos y widgets del formulario."""
        model = MaterialProyecto
        fields = ['cantidad_utilizada', 'notas']
        widgets = {
            'cantidad_utilizada': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['cantidad_utilizada'].widget.attrs['max'] = self.instance.cantidad_asignada
            self.fields['cantidad_utilizada'].help_text = f'Máximo: {
                self.instance.cantidad_asignada}'

# ────────────────────────────────────────────────────────────────────────────────
# FORMULARIO: Configuración del Sistema
# ────────────────────────────────────────────────────────────────────────────────
class ConfiguracionSistemaForm(forms.Form):
    """Formulario para configurar parámetros del sistema."""
    # Definición de campos del formulario
    umbral_stock_critico = forms.IntegerField(
        label="Umbral de Stock Crítico",
        min_value=1, max_value=100, initial=10,
        help_text="Nivel bajo crítico para activar alertas urgentes.",
    )
    umbral_stock_bajo = forms.IntegerField(
        label="Umbral de Stock Bajo",
        min_value=1, max_value=100, initial=30,
        help_text="Nivel de stock bajo recomendado para reorden.",
    )
    modo_mantenimiento = forms.BooleanField(
        label="Modo Mantenimiento", required=False,
        help_text="Habilita o deshabilita el modo de mantenimiento.",
    )
    auto_generar_orden_compra = forms.BooleanField(
        label="Generar Orden de Compra Automáticamente", required=False,
        help_text="Activa la generación automática de órdenes de compra.",
    )
    proveedor_default = forms.CharField(
        label="Proveedor Predeterminado",
        max_length=100, required=True,
        help_text="Nombre del proveedor por defecto.",
    )
    registro_de_auditorias = forms.BooleanField(
        label="Activar Registro de Auditorías", required=False,
        help_text="Activa el registro de acciones en el sistema.",
    )
    mostrar_mensaje_bienvenida = forms.BooleanField(
        label="Mostrar Mensaje de Bienvenida", required=False,
        help_text="Muestra un mensaje al ingresar al sistema.",
    )
    formato_fecha_preferido = forms.ChoiceField(
        label="Formato de Fecha Preferido",
        choices=[
            ("%d/%m/%Y", "DD/MM/AAAA"),
            ("%m/%d/%Y", "MM/DD/AAAA"),
            ("%Y-%m-%d", "AAAA-MM-DD"),
        ],
        help_text="Formato de fecha que se mostrará en reportes.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        configuraciones = {cfg.clave: cfg.valor for cfg in ConfiguracionSistema.objects.all()}# pylint: disable=no-member
        for clave in self.fields:
            if clave in configuraciones:
                valor = configuraciones[clave]
                campo = self.fields[clave]
                if isinstance(campo, forms.BooleanField):
                    campo.initial = valor in ["True", "true", "1"]
                elif isinstance(campo, forms.IntegerField):
                    try:
                        campo.initial = int(valor)
                    except ValueError:
                        campo.initial = campo.initial
                else:
                    campo.initial = valor

    def clean(self):
        cleaned_data = super().clean()
        critico = cleaned_data.get('umbral_stock_critico')
        bajo = cleaned_data.get('umbral_stock_bajo')
        if critico is not None and bajo is not None and critico >= bajo:
            raise forms.ValidationError("El umbral crítico debe ser menor que el umbral bajo.")
        return cleaned_data

    def guardar(self):
        """Guarda los valores del formulario en la base de datos."""
        for clave, valor in self.cleaned_data.items():
            ConfiguracionSistema.objects.update_or_create( # pylint: disable=no-member
                clave=clave,
                defaults={"valor": str(valor)},
            )
class InformeInventarioFiltroForm(forms.Form):
    """Formulario para filtrar productos en el informe de inventario."""
    ubicacion = forms.ChoiceField(required=False, label='Ubicación')
    categoria = forms.ChoiceField(required=False, choices=[], label='Categoría')
    proveedor = forms.ChoiceField(required=False, label='Proveedor')
    stock_min = forms.IntegerField(required=False, label='Stock mínimo (desde)')
    stock_max = forms.IntegerField(required=False, label='Stock máximo (hasta)')

    # Estos quedan en el formulario, pero no se mostrarán de momento
    fecha_inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    fecha_fin = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Opciones dinámicas
        categorias = (
            Producto.objects # pylint: disable=no-member
            .values_list('categoria', flat=True)
            .exclude(categoria__isnull=True)
            .exclude(categoria__exact='')
            .distinct()
            .order_by('categoria')
        )
        ubicaciones = (
            Producto.objects # pylint: disable=no-member
            .values_list('ubicacion', flat=True)
            .exclude(ubicacion__isnull=True)
            .exclude(ubicacion__exact='')
            .distinct()
            .order_by('ubicacion')
        )
        proveedores = (
            Producto.objects# pylint: disable=no-member
            .filter(proveedor__isnull=False)
            .values_list('proveedor__id', 'proveedor__nombre')
            .distinct()
            .order_by('proveedor__nombre')
        )

        self.fields['categoria'].choices = [('', 'Todas')] + [(c, c) for c in categorias]
        self.fields['ubicacion'].choices = [('', 'Todas')] + [(u, u) for u in ubicaciones]
        self.fields['proveedor'].choices = [('', 'Todos')] + [(str(p[0]),
                                                               p[1]) for p in proveedores]

    def clean_stock_min(self):
        """Valida el campo de stock mínimo."""
        valor = self.cleaned_data.get('stock_min')
        if valor is not None and valor < 0:
            raise forms.ValidationError("El stock mínimo no puede ser negativo.")
        return None if valor == 0 else valor

    def clean_stock_max(self):
        """Valida el campo de stock máximo."""
        valor = self.cleaned_data.get('stock_max')
        if valor is not None and valor < 0:
            raise forms.ValidationError("El stock máximo no puede ser negativo.")
        return None if valor == 0 else valor
