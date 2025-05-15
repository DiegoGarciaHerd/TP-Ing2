from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class Usuario(AbstractUser):
    username = None  # Eliminamos el campo username original
    email = models.EmailField(_('email address'), unique=True)

    ROLES = (
        ('ADMIN', 'Administrador'),
        ('EMPLEADO', 'Empleado'),
        ('CLIENTE', 'Cliente'),
    )
    rol = models.CharField(max_length=10, choices=ROLES, default='CLIENTE')
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)

    USERNAME_FIELD = 'email'  # Usamos email para login
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Campos obligatorios al crear superusuario

    def __str__(self):
        return self.get_full_name() or self.email