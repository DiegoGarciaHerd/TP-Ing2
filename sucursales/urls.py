from django.urls import path
from . import views 
app_name = 'sucursales' 

urlpatterns = [
    path('', views.SucursalListView.as_view(), name='lista_sucursales'),
    path('<int:sucursal_id>/vehiculos/', views.VehiculoListView.as_view(), name='vehiculos_por_sucursal'),
    path('vehiculo/<int:pk>/', views.VehiculoDetailView.as_view(), name='vehiculo_detail'),
]