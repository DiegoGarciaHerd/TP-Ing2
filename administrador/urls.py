from django.urls import path
from .views.auth import (
    login_admin_step1 as admin_login,
    login_admin_step2,
    admin_menu,
    admin_logout,
    reset_admin_balance,
)
from .views.vehiculos import (
    cargar_autos,
    modificar_autos,
    borrar_autos,
    #ver_autos,
    obtener_datos_vehiculo,
    #toggle_disponibilidad,
    gestionar_vehiculos
)
from .views.empleados import (
    cargar_empleados, 
    modificar_empleado, 
    ListarEmpleadosView,
    borrar_empleado
)

from .views.sucursal import (
    cargar_sucursal,
    modificar_sucursal,
    borrar_sucursal,
    obtener_datos_sucursal,
    listado_sucursales,
)

from .views import reservas
from .views.estadisticas_autos import estadisticas_autos, estadisticas_tipos_autos

urlpatterns = [
    path('', admin_menu, name='admin_menu'),  
    path('login/', admin_login, name='admin_login_step1'),  
    path('verificar/', login_admin_step2, name='admin_login_step2'),  
    path('logout/', admin_logout, name='admin_logout'),

    # URLs de Vehiculos
    path('carga-autos/', cargar_autos, name="cargar_autos"),
    path('modificar-autos/', modificar_autos, name="modificar_autos"),
    path('borrar-autos/', borrar_autos, name="borrar_autos"),
    path('obtener-datos-vehiculo/', obtener_datos_vehiculo, name="obtener_datos_vehiculo"),
    
    # URLs de Empleados
    path('cargar-empleados/', cargar_empleados, name="cargar_empleados"),
    path('modificar-empleado/', modificar_empleado, name="modificar_empleado"),
    path('listar-empleados/', ListarEmpleadosView.as_view(), name="listar_empleados"),
    path('borrar-empleado/', borrar_empleado, name="borrar_empleado"),
    
    # URLs de Sucursales
    path('cargar-sucursal/', cargar_sucursal, name="cargar_sucursal"),
    path('modificar-sucursal/', modificar_sucursal, name="modificar_sucursal"),
    path('borrar-sucursal/', borrar_sucursal, name="borrar_sucursal"),
    path('listado_sucursales/', listado_sucursales, name="listado_sucursales"),

    path('obtener-datos-sucursal/', obtener_datos_sucursal, name='obtener_datos_sucursal'), 
    path('reset-balance/', reset_admin_balance, name='reset_admin_balance'),
    path('detalle-ingresos-reservas/', reservas.detalle_ingresos_reservas, name='detalle_ingresos_reservas'),
    path('estadisticas-adicionales/', reservas.estadisticas_adicionales, name='estadisticas_adicionales'),
    path('estadisticas-autos/', estadisticas_autos, name='estadisticas_autos'),
    path('estadisticas-tipos-autos/', estadisticas_tipos_autos, name='estadisticas_tipos_autos'),
    path('gestion-vehiculos/', gestionar_vehiculos, name='gestionar_vehiculos'),
    
]