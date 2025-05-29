from django.urls import path
from .views import (
    login_admin_step1,
    login_admin_step2,
    admin_logout,
    admin_menu,
    cargar_autos,
    borrar_autos,
    modificar_autos,
    cargar_empleados
)

urlpatterns = [
<<<<<<< HEAD
    path('login/', views.login_admin_step1, name='admin_login_step1'),
    path('verificar/', views.login_admin_step2, name='admin_login_step2'),
    path('menu-admin/', views.admin_menu, name="admin_menu"),
    path('carga-autos/', views.cargar_autos, name="cargar_autos"),
    path('borrar-autos/', views.borrar_autos, name="borrar_autos"),
    path('carga-empleados/', views.cargar_empleados, name="cargar_empleados"),
    path('modificar-autos/', views.modificar_autos, name="modificar_autos"),
    path('ver-autos/', views.ver_autos, name="ver_autos")
=======
    path('login/', login_admin_step1, name='admin_login_step1'),
    path('verificar/', login_admin_step2, name='admin_login_step2'),
    path('menu-admin/', admin_menu, name="admin_menu"),
    path('carga-autos/', cargar_autos, name="cargar_autos"),
    path('borrar-autos/', borrar_autos, name="borrar_autos"),
    path('carga-empleados/', cargar_empleados, name="cargar_empleados"),
    path('modificar-autos/', modificar_autos, name="modificar_autos"),
    path('logout/', admin_logout, name='admin_logout'),
>>>>>>> 27f29f389c8f9595a4b215430fc39597d1ba2d4b
]