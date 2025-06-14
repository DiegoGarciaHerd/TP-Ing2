from django.urls import path
from . import views

app_name = 'reservas'

urlpatterns = [
    path('crear/<int:vehiculo_id>/', views.crear_reserva, name='crear_reserva'),
    path('ticket/<int:vehiculo_id>/', views.ticket_reserva, name='ticket_reserva'),
    path('seleccionar-metodo-pago/<int:vehiculo_id>/', views.seleccionar_metodo_pago, name='seleccionar_metodo_pago'),
    path('pagar/<int:vehiculo_id>/', views.procesar_pago, name='procesar_pago'),
    path('confirmar/<int:vehiculo_id>/', views.confirmar_reserva, name='confirmar_reserva'),
    path('mis_reservas/', views.mis_reservas, name='mis_reservas'),
    path('reserva/<int:reserva_id>/', views.detalle_reserva, name='detalle_reserva'),
    path('reserva/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('reserva/<int:reserva_id>/actualizar-extras/', views.actualizar_extras, name='actualizar_extras'),
]