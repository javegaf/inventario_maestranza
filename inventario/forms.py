"""
Formularios del módulo de inventario.
Este archivo contiene los formularios ModelForm utilizados para crear y editar
productos, movimientos de inventario, proveedores y kits de productos.
"""

from django.utils import timezone
from django import forms
from .models import Producto, MovimientoInventario, Proveedor, KitProducto

class ProductoForm(forms.ModelForm):
    """Formulario para crear o actualizar un producto del inventario."""

    class Meta:
        """Define el modelo y los campos usados en el formulario de Producto."""
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



class ProductoEditableForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'numero_serie', 'ubicacion', 'categoria', 'proveedor', 'fecha_vencimiento', 'stock_actual', 'stock_minimo']
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

        # Campos que NO se deben editar (los deshabilitamos)
        campos_no_editables = ['nombre', 'numero_serie', 'categoria']
        for campo in campos_no_editables:
            self.fields[campo].disabled = True
            self.fields[campo].widget.attrs.update({
                'readonly': True,
                'class': 'form-control bg-secondary-subtle text-dark'
            })

        # Estilo común para todos los campos
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')

