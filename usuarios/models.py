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
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser debe tener is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser debe tener is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

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

    USERNAME_FIELD = 'email'  
    REQUIRED_FIELDS = ['first_name', 'last_name'] 

    objects = UsuarioManager()

    def __str__(self):
        return self.get_full_name() or self.email
    

