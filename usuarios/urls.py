from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('editar-perfil/', views.editar_perfil, name='editar_perfil'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
]



