from django.urls import path
from .views import (menu_empleado
    )

urlpatterns = [
    path('/menu-empleados', menu_empleado, name='menu_empleados'),
    # Aquí puedes agregar más URLs específicas para las vistas de empleados
]