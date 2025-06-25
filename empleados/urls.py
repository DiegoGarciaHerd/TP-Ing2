from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    path('menu/', views.menu_empleado, name='menu_empleado'),
    path('login/', views.login_empleado, name='login_empleado'),
    path('buscar_cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('modificar_autos/', views.modificar_autos, name='modificar_autos'),
    path('reserva_empleado/', views.reserva_empleado, name='reserva_empleado'),
    path('retiros-pendientes/', views.listar_retiros_pendientes, name='listar_retiros_pendientes'),
    path('confirmar-retiro/<int:reserva_id>/', views.confirmar_retiro_auto, name='confirmar_retiro_auto'),
    path('obtener-datos-vehiculo-ajax/', views.obtener_datos_vehiculo_ajax, name='obtener_datos_vehiculo_ajax'), 
    path('devoluciones-pendientes/', views.listar_devoluciones_pendientes, name='listar_devoluciones_pendientes'),
    path('confirmar-devolucion/<int:reserva_id>/', views.confirmar_devolucion_auto, name='confirmar_devolucion_auto'),


]