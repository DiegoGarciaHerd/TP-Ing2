from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('buscar-vehiculos/', views.buscar_vehiculos, name='buscar_vehiculos'),
]