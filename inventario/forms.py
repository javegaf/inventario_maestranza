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

class MovimientoFiltroForm(forms.Form):
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
