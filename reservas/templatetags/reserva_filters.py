from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """Divide un string usando el argumento como separador"""
    return value.split(arg) 