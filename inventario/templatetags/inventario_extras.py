"""Este módulo contiene filtros personalizados para Django templates."""
from django import template


register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def currency(value):
    """Format value as currency."""
    try:
        if value is None:
            return "$0.00"
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@register.filter
def percentage(value):
    """Format value as percentage."""
    try:
        if value is None:
            return "0.0%"
        return f"{float(value):.1f}%"
    except (ValueError, TypeError):
        return "0.0%"

@register.filter
def abs_value(value):
    """Return absolute value."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    return value - arg

@register.filter
def clp(value):
    """
    Formatea un valor numérico como CLP: con separadores de miles y sin decimales.
    Ejemplo: 7979419.56 → $7.979.420
    """
    try:
        formatted = f"${float(value):,.0f}".replace(",", ".")
        return formatted
    except (ValueError, TypeError):
        return "$0"

@register.filter
def get_estado_color(value):
    colores = {
        'sugerida': 'warning',
        'pendiente': 'info',
        'aprobada': 'primary',
        'recepcionada': 'success',
        'cancelada': 'secondary',
    }
    return colores.get(value, 'light')