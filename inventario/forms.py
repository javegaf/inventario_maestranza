"""
Formularios del módulo de inventario.
Este archivo contiene los formularios ModelForm utilizados para crear y editar
productos, movimientos de inventario, proveedores y kits de productos.
"""

from django import forms
from .models import Producto, MovimientoInventario, Proveedor, KitProducto

class ProductoForm(forms.ModelForm):
    """Formulario para crear o actualizar un producto del inventario."""

    class Meta:
        """Define el modelo y los campos usados en el formulario de Producto."""
        model = Producto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Taladro eléctrico'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Especifica los detalles del producto'}),
            'ubicacion': forms.TextInput(attrs={'placeholder': 'Ej. Bodega A, estante 3'}),
            'categoria': forms.TextInput(attrs={'placeholder': 'Ej. Herramientas'}),
            'fecha_vencimiento': forms.DateInput(attrs={'placeholder': 'DD/MM/AAAA', 'type': 'date'}),
            'stock_actual': forms.NumberInput(attrs={'placeholder': 'Cantidad en inventario'}),
            'stock_minimo': forms.NumberInput(attrs={'placeholder': 'Cantidad mínima'}),
            'precio': forms.NumberInput(attrs={'placeholder': 'Ej. 19990'}),
            'numero_serie': forms.TextInput(attrs={'placeholder': 'Ej. SN123456789'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class MovimientoInventarioForm(forms.ModelForm):
    """Formulario para registrar movimientos de inventario (entrada, salida, ajuste)."""

    class Meta:
        """Define el modelo y los campos usados en el formulario de MovimientoInventario."""
        model = MovimientoInventario
        fields = '__all__'

class ProveedorForm(forms.ModelForm):
    """Formulario para registrar o editar información de proveedores."""

    class Meta:
        """Define el modelo y los campos usados en el formulario de Proveedor."""
        model = Proveedor
        fields = '__all__'

class KitProductoForm(forms.ModelForm):
    """Formulario para crear kits de productos agrupando varios ítems."""

    class Meta:
        """Define el modelo y los campos usados en el formulario de KitProducto."""
        model = KitProducto
        fields = '__all__'
