from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_admin_step1, name='admin_login_step1'),
    path('verificar/', views.login_admin_step2, name='admin_login_step2'),
    path('menu-admin/', views.admin_menu, name="admin_menu"),
    path('cargar-autos/', views.cargar_autos, name='cargar_autos')
]