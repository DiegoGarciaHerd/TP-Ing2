from django.urls import path
from . import views

app_name = 'empleados' # Muy importante para el uso de {% url 'empleados:menu_empleado' %}

urlpatterns = [
    path('menu/', views.menu_empleado, name='menu_empleado'),
    # Agrega aquí las URLs para las otras vistas de empleado
    path('login/', views.login_empleado, name='login_empleado'), # Si usas un login específico de empleado
    path('buscar_cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('modificar_vehiculo/', views.modificar_vehiculo, name='modificar_vehiculo'),
    path('reserva_empleado/', views.reserva_empleado, name='reserva_empleado'),
]