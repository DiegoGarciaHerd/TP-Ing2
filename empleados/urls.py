from django.urls import path
from . import views

app_name = 'empleados'

urlpatterns = [
    path('menu/', views.menu_empleado, name='menu_empleado'),
    path('login/', views.login_empleado, name='login_empleado'),
    path('buscar_cliente/', views.buscar_cliente, name='buscar_cliente'),
    path('modificar_autos/', views.modificar_autos, name='modificar_autos'),
    path('reserva_empleado/', views.reserva_empleado, name='reserva_empleado'),
]