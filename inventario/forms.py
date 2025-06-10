"""
Formularios del módulo de inventario.
Este archivo contiene los formularios ModelForm utilizados para crear y editar
productos, movimientos de inventario, proveedores y kits de productos.
"""

from django.utils import timezone
from django import forms
from .models import (
    Producto, MovimientoInventario, Proveedor, KitProducto,
    CompraProveedor, EvaluacionProveedor
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
    """Formulario para registrar movimientos de inventario."""

    class Meta:
        model = MovimientoInventario
        fields = '__all__'


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
