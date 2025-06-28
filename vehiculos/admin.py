from django.contrib import admin
from .models import Vehiculo
@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'modelo', 'patente', 'sucursal_actual', 'estado', 'precio_por_dia')  # Quitar 'disponible'
    list_filter = ('sucursal_actual', 'estado')  # Cambiar 'disponible' por 'estado'
    list_editable = ('estado', 'precio_por_dia')  # Quitar 'disponible'
    search_fields = ('marca', 'modelo', 'patente')
    ordering = ('marca', 'modelo')