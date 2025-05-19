from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('El Email debe ser proporcionado'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'ADMIN')
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)  # Necesario para acceso a /admin
        extra_fields.setdefault('is_superuser', True)  # Necesario para permisos totales

        return self.create_user(email, password, **extra_fields)


class Usuario(AbstractUser):
    username = None  # Eliminamos username
    email = models.EmailField(_('email address'), unique=True)
    edad = models.PositiveIntegerField(null=True)
    DNI = models.CharField(max_length=10, unique=True, null=True)

    ROLES = (
        ('ADMIN', 'Administrador'),
        ('CLIENTE', 'Cliente'),
        ('EMPLEADO', 'Empleado')
    )
    rol = models.CharField(max_length=10, choices=ROLES, default='CLIENTE')

    # Estos campos deben ser campos reales, no propiedades
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UsuarioManager()

    def __str__(self):
        return self.get_full_name() or self.email

    # Propiedades lógicas adicionales (no sobreescriben los campos)
    @property
    def is_admin(self):
        return self.rol == 'ADMIN' or self.is_superuser

    @property
    def is_empleado(self):
        return self.rol == 'EMPLEADO'
