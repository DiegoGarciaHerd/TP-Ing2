from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(value, arg):
    """Añade la clase CSS especificada al campo de formulario"""
    return value.as_widget(attrs={'class': arg}) 