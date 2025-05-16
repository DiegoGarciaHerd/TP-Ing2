from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_vehiculos, name='lista_vehiculos'),
    path('<int:pk>/', views.detalle_vehiculo, name='detalle_vehiculo'),
    #path('lista/', views.lista_vehiculos, name='lista_vehiculos'),
    ]