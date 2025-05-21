from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [

    path('crear/<int:vehiculo_id>/', views.crear_reserva, name='crear_reserva'), 
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('mis_reservas/<int:reserva_id>/', views.detalle_reserva, name='detalle_reserva'),
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar_reserva'),
]