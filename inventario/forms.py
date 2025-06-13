"""
Formularios del módulo de inventario.
Este archivo contiene los formularios ModelForm utilizados para crear y editar
productos, movimientos de inventario, proveedores y kits de productos.
"""

from django.utils import timezone
from django import forms
from .models import (
    Producto, MovimientoInventario, Proveedor, KitProducto,
    CompraProveedor, EvaluacionProveedor, LoteProducto, HistorialLote
)


class ProductoForm(forms.ModelForm):
    """Formulario para crear o actualizar un producto del inventario."""

    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': timezone.now().date().isoformat()
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['fecha_vencimiento'].widget.attrs['min'] = timezone.now().date().isoformat()


class ProductoEditableForm(forms.ModelForm):
    """Formulario para editar un producto sin permitir cambios en ciertos campos."""

    class Meta:
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
                self.fields['lote'].queryset = LoteProducto.objects.filter(
                    producto_id=producto_id, 
                    activo=True
                ).order_by('fecha_vencimiento')
            except (ValueError, TypeError):
                self.fields['lote'].queryset = LoteProducto.objects.none()
        elif self.instance.pk:
            self.fields['lote'].queryset = LoteProducto.objects.filter(
                producto=self.instance.producto, 
                activo=True
            ).order_by('fecha_vencimiento')
        else:
            self.fields['lote'].queryset = LoteProducto.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        lote = cleaned_data.get('lote')
        tipo = cleaned_data.get('tipo')
        cantidad = cleaned_data.get('cantidad')
        
        # Validate that lote belongs to the selected product
        if lote and producto and lote.producto != producto:
            raise forms.ValidationError('El lote seleccionado no pertenece al producto seleccionado.')
        
        # Validate stock for salida movements
        if tipo == 'salida' and cantidad:
            if lote:
                if cantidad > lote.cantidad_actual:
                    raise forms.ValidationError(f'No hay suficiente stock en el lote {lote.numero_lote}. Disponible: {lote.cantidad_actual}')
            elif producto:
                if cantidad > producto.stock_actual:
                    raise forms.ValidationError(f'No hay suficiente stock del producto. Disponible: {producto.stock_actual}')
        
        return cleaned_data


class MovimientoFiltroForm(forms.Form):
    """Formulario para filtrar movimientos por fecha, tipo y producto."""

    fecha_inicio = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    tipo_movimiento = forms.ChoiceField(
        choices=[('', 'Todos')] + MovimientoInventario.TIPO_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        required=False,
        empty_label="Todos los productos",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CompraProveedorForm(forms.ModelForm):
    """Formulario para registrar compras a proveedores."""

    class Meta:
        model = CompraProveedor
        fields = ['producto', 'cantidad', 'precio_unitario', 'numero_factura']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_unitario': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'numero_factura': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EvaluacionProveedorForm(forms.ModelForm):
    """Formulario para registrar evaluaciones de proveedores."""

    class Meta:
        model = EvaluacionProveedor
        fields = ['calificacion', 'comentario']
        widgets = {
            'calificacion': forms.Select(attrs={'class': 'form-control'}),
            'comentario': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class ProveedorForm(forms.ModelForm):
    """Formulario para registrar o editar proveedores."""

    class Meta:
        model = Proveedor
        fields = '__all__'


class KitProductoForm(forms.ModelForm):
    """Formulario para crear kits de productos."""

    class Meta:
        model = KitProducto
        fields = '__all__'


class LoteProductoForm(forms.ModelForm):
    """Formulario para crear/editar lotes de productos."""
    
    class Meta:
        model = LoteProducto
        fields = ['numero_lote', 'fecha_vencimiento', 'cantidad_inicial', 'observaciones']
        widgets = {
            'fecha_vencimiento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'numero_lote': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: LT-2025-001'}),
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
    
    estado = forms.ChoiceField(choices=ESTADO_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    fecha_vencimiento_desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    fecha_vencimiento_hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
