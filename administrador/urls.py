from django.urls import path
from .views.auth import (
    login_admin_step1 as admin_login,
    login_admin_step2,
    admin_menu,
    admin_logout,
)
from .views.vehiculos import (
    cargar_autos,
    modificar_autos,
    borrar_autos,
    ver_autos,
    obtener_datos_vehiculo,
    toggle_disponibilidad
)
from .views.empleados import (
    cargar_empleados, 
    modificar_empleados, 
    ListarEmpleadosView,
    borrar_empleado
)

from .views.sucursal import (
    cargar_sucursal,
    modificar_sucursal,
    borrar_sucursal,
    obtener_datos_sucursal
)

urlpatterns = [
    path('', admin_menu, name='admin_menu'),  
    path('login/', admin_login, name='admin_login_step1'),  
    path('verificar/', login_admin_step2, name='admin_login_step2'),  
    path('logout/', admin_logout, name='admin_logout'),

    # URLs de Vehiculos
    path('carga-autos/', cargar_autos, name="cargar_autos"),
    path('modificar-autos/', modificar_autos, name="modificar_autos"),
    path('borrar-autos/', borrar_autos, name="borrar_autos"),
    path('ver-autos/', ver_autos, name="ver_autos"),
    path('obtener-datos-vehiculo/', obtener_datos_vehiculo, name="obtener_datos_vehiculo"),
    path('ver-autos/<int:vehiculo_id>/toggle-disponibilidad/', toggle_disponibilidad, name="toggle_disponibilidad"),
    
    # URLs de Empleados
    path('cargar-empleados/', cargar_empleados, name="cargar_empleados"),
    path('modificar-empleados/', modificar_empleados, name="modificar_empleados"),
    path('listar-empleados/', ListarEmpleadosView.as_view(), name="listar_empleados"),
    path('borrar-empleado/', borrar_empleado, name="borrar_empleado"),
    
    # URLs de Sucursales
    path('cargar-sucursal/', cargar_sucursal, name="cargar_sucursal"),
    path('modificar-sucursal/', modificar_sucursal, name="modificar_sucursal"),
    path('borrar-sucursal/', borrar_sucursal, name="borrar_sucursal"),

    path('obtener-datos-sucursal/', obtener_datos_sucursal, name='obtener_datos_sucursal'), 
]