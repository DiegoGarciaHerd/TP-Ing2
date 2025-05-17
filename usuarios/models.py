from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class Usuario(AbstractUser):
    username = None  # Eliminamos el campo username original
    email = models.EmailField(_('email address'), unique=True)
    edad = models.PositiveIntegerField(null=True)
    DNI = models.CharField(max_length=10, unique=True, null=True)

    ROLES = (
        ('ADMIN', 'Administrador'),
        ('CLIENTE', 'Cliente'),
    )
    rol = models.CharField(max_length=10, choices=ROLES, default='CLIENTE')

    USERNAME_FIELD = 'email'  # Usamos email para login
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Campos obligatorios al crear superusuario

    def __str__(self):
        return self.get_full_name() or self.email