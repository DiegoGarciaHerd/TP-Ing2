from django import template
from datetime import date

register = template.Library()

@register.filter
def split(value, arg):
    """Divide un string usando el argumento como separador"""
    return value.split(arg)

@register.filter
def dias_duracion(fecha_devolucion, fecha_recogida):
    if isinstance(fecha_devolucion, date) and isinstance(fecha_recogida, date):
        dias = (fecha_devolucion - fecha_recogida).days
        return 1 if dias == 0 else dias
    return 0 