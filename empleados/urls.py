from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    path('menu/', views.menu_empleado, name='menu_empleado'),
    path('buscar_cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('modificar_autos/', views.modificar_autos, name='modificar_autos'),
    path('reserva_empleado/', views.empleados_seleccionar_vehiculo, name='seleccionar_vehiculo_para_reserva'),
    path('retiros-pendientes/', views.listar_retiros_pendientes, name='listar_retiros_pendientes'),
    path('confirmar-retiro/<int:reserva_id>/', views.confirmar_retiro_auto, name='confirmar_retiro_auto'),
    path('obtener-datos-vehiculo-ajax/', views.obtener_datos_vehiculo_ajax, name='obtener_datos_vehiculo_ajax'), 
    path('devoluciones-pendientes/', views.listar_devoluciones_pendientes, name='listar_devoluciones_pendientes'),
    path('confirmar-devolucion/<int:reserva_id>/', views.confirmar_devolucion_auto, name='confirmar_devolucion_auto'),
    path('registrar-cliente/', views.registrar_cliente, name='registrar_cliente'),
    path('editar-perfil/', views.editar_perfil_empleado, name='editar_perfil_empleado'),
    path('reservar/<int:vehiculo_id>/', views.empleados_crear_reserva, name='crear_reserva_empleado'),
    
]