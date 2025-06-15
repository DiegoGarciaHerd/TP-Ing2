from django.urls import path
from .views import (menu_empleado,
    login_empleado,
    buscar_cliente,
    modificar_vehiculo,
    reserva_empleado)

urlpatterns = [
    path('menu-empleados/', menu_empleado, name='menu_empleado'),
    path('empleado-auth/', login_empleado, name='login_empleado'),
    path('buscar-cliente/', buscar_cliente, name='buscar_cliente'),
    path('modificar-vehiculo/', modificar_vehiculo, name='modificar_vehiculo'),
    path('reserva-empleado/', reserva_empleado, name='reserva_empleado')
]