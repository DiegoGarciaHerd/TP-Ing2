from django.contrib import admin
from .models import Reserva
from vehiculos.models import Vehiculo

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'vehiculo', 'fecha_recogida', 'fecha_devolucion', 'costo_base', 'monto_adicional', 'costo_total', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_recogida', 'fecha_devolucion', 'vehiculo__sucursal_actual')
    search_fields = ('cliente__email', 'vehiculo__patente', 'vehiculo__marca', 'vehiculo__modelo')
    raw_id_fields = ('cliente', 'vehiculo')
    readonly_fields = ('costo_base', 'monto_adicional', 'costo_total', 'fecha_creacion')