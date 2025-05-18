from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_admin_step1, name='admin_login_step1'),
    path('verificar/', views.login_admin_step2, name='admin_login_step2'),
]