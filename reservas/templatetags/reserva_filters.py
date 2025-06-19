from django import template
from datetime import date, datetime

register = template.Library()

@register.filter
def split(value, arg):
    """Divide un string usando el argumento como separador"""
    return value.split(arg)

@register.filter
def multiply(value, arg):
    """Multiplies the value by the argument"""
    try:
        return round(float(value) * float(arg))
    except (ValueError, TypeError):
        return ''

@register.filter
def dias_duracion(fecha_devolucion, fecha_recogida):
    """Calcula la duración en días entre dos fechas"""
    if isinstance(fecha_devolucion, str):
        fecha_devolucion = datetime.strptime(fecha_devolucion, '%Y-%m-%d')
    if isinstance(fecha_recogida, str):
        fecha_recogida = datetime.strptime(fecha_recogida, '%Y-%m-%d')
    return (fecha_devolucion - fecha_recogida).days

@register.filter
def subtract(value, arg):
    """Subtracts the argument from the value"""
    try:
        return round(float(value) - float(arg))
    except (ValueError, TypeError):
        return value

@register.filter
def div(value, arg):
    """Divides the value by the argument"""
    try:
        if float(arg) == 0:
            return 0
        return round(float(value) / float(arg))
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Adds the argument to the value"""
    try:
        return round(float(value) + float(arg))
    except (ValueError, TypeError):
        return value 