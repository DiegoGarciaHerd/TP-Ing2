from django.urls import path
from .views.auth import (
    login_admin_step1,
    login_admin_step2,
    admin_logout,
    admin_menu
)
from .views.vehiculos import (
    cargar_autos,
    borrar_autos,
    modificar_autos,
    ver_autos
)
from .views.empleados import cargar_empleados

urlpatterns = [
    path('login/', login_admin_step1, name='admin_login_step1'),
    path('verificar/', login_admin_step2, name='admin_login_step2'),
    path('menu-admin/', admin_menu, name="admin_menu"),
    path('carga-autos/', cargar_autos, name="cargar_autos"),
    path('borrar-autos/', borrar_autos, name="borrar_autos"),
    path('carga-empleados/', cargar_empleados, name="cargar_empleados"),
    path('modificar-autos/', modificar_autos, name="modificar_autos"),
    path('ver-autos/', ver_autos, name="ver_autos"),
    path('logout/', admin_logout, name='admin_logout'),
]