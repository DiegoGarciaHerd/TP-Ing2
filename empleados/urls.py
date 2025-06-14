from django.urls import path
from .views import menu_empleados

urlpatterns = [
    path('/menu-empleados', menu_empleados, name='menu_empleados'),
    # Aquí puedes agregar más URLs específicas para las vistas de empleados
]