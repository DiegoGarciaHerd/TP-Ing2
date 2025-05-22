from django.contrib import admin
from .models import Vehiculo

@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'modelo', 'patente', 'precio_por_dia', 'sucursal_actual', 'disponible')
    list_filter = ('sucursal_actual', 'disponible')
    search_fields = ('marca', 'modelo', 'patente')
    list_editable = ('disponible',)