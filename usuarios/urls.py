from django.urls import path
from . import views
from .views import UsuarioLoginView

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', UsuarioLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('forma-pago/', views.gestionar_forma_pago, name='gestionar_forma_pago'),
    path('agregar-tarjeta/', views.agregar_tarjeta, name='agregar_tarjeta'),
]

