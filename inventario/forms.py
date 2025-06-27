"""
Formularios del módulo de inventario.
Este archivo contiene los formularios ModelForm utilizados para crear y editar
productos, movimientos de inventario, proveedores y kits de productos.
"""

import re
import uuid
from django.utils import timezone
from django.forms import ValidationError, inlineformset_factory
from django import forms
from django.core.validators import RegexValidator
from .models import (
    Producto, MovimientoInventario, Proveedor, KitProducto,ProductoEnKit,
    CompraProveedor, EvaluacionProveedor, LoteProducto, HistorialLote
)


class ProductoForm(forms.ModelForm):
    """Formulario para crear o actualizar un producto del inventario."""

    class Meta:
        model = Producto
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'placeholder': 'Ej. Taladro eléctrico'}),
            'descripcion': forms.Textarea(attrs={'placeholder': 'Especifica los detalles del producto'}),
            'ubicacion': forms.TextInput(attrs={'placeholder': 'Ej. Bodega A, estante 3'}),
            'categoria': forms.TextInput(attrs={'placeholder': 'Ej. Herramientas'}),
            'fecha_vencimiento': forms.DateInput(attrs={'placeholder': 'DD/MM/AAAA', 'type': 'date', 'class': 'form-control', 'min': timezone.now().date().isoformat()}),
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
    codigo_editable = forms.CharField(
        required=False,
        label="Código del Kit (editable)",
        help_text="El código comienza con KST-. Puedes editar la parte después del guión.",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese sufijo (ej: ABC123)'
        }),
        validators=[
            RegexValidator(
                regex='^[A-Z0-9-]*$',
                message='Solo se permiten letras mayúsculas, números y guiones',
                code='invalid_code'
            )
        ]
    )

    class Meta:
        model = KitProducto
        fields = ['nombre', 'categoria', 'descripcion', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Kit de mantenimiento preventivo'
            }),
            'categoria': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Kits de repuestos'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del kit'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            if self.instance.codigo and self.instance.codigo.startswith('KST-'):
                self.fields['codigo_editable'].initial = self.instance.codigo[4:]
            
            self.fields['codigo_mostrar'] = forms.CharField(
                initial=self.instance.codigo,
                label="Código Completo",
                required=False,
                widget=forms.TextInput(attrs={
                    'class': 'form-control bg-light',
                    'readonly': True
                })
            )

    def clean(self):
        cleaned_data = super().clean()
        # Eliminar validación de código aquí (se maneja en save())
        return cleaned_data

    def clean_codigo_editable(self):
        codigo_editable = self.cleaned_data.get('codigo_editable', '').strip().upper()
        
        if codigo_editable:
            if codigo_editable.startswith('KST-'):
                codigo_editable = codigo_editable[4:]
            
            if not re.match('^[A-Z0-9-]*$', codigo_editable):
                raise ValidationError("Solo se permiten letras mayúsculas, números y guiones")
        
        return codigo_editable

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Debug: Mostrar estado antes de guardar
        print(f"Guardando kit. Instancia nueva: {not instance.pk}")
        print(f"Datos codigo_editable: {self.cleaned_data.get('codigo_editable')}")

        # Generación del código
        codigo_editable = self.cleaned_data.get('codigo_editable', '').strip()
        instance.codigo = f"KST-{codigo_editable if codigo_editable else uuid.uuid4().hex[:6].upper()}"
        
        # Debug: Mostrar código generado
        print(f"Código generado: {instance.codigo}")

        if commit:
            try:
                instance.save()
                print("¡Kit guardado exitosamente!")
            except Exception as e:
                print(f"Error al guardar: {str(e)}")
                raise
        
        return instance


class ProductoEnKitForm(forms.ModelForm):
    class Meta:
        model = ProductoEnKit
        fields = ['producto', 'cantidad']
        widgets = {
            'producto': forms.Select(attrs={
                'class': 'form-select producto-select',
                'data-live-search': 'true'
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Cantidad',
                'min': 1
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(
            stock_actual__gt=0
        ).exclude(
            auditoriainventario__bloqueado=True
        ).distinct().order_by('nombre')

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and cantidad:
            if producto.stock_actual < cantidad:
                self.add_error(
                    'cantidad', 
                    f"Stock insuficiente. Disponible: {producto.stock_actual}"
                )
            if producto.is_blocked:
                self.add_error(
                    'producto',
                    "Este producto está actualmente bloqueado"
                )
        return cleaned_data


# Configuración del FormSet
ProductoEnKitFormSet = inlineformset_factory(
    KitProducto,
    ProductoEnKit,
    form=ProductoEnKitForm,
    fields=('producto', 'cantidad'),
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


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
