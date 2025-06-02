from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from cryptography.fernet import Fernet
from django.conf import settings
import os


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

    @property
    def tiene_reservas_activas(self):
        """Verifica si el usuario tiene reservas activas o pendientes"""
        return self.reservas.filter(estado__in=['CONFIRMADA', 'PENDIENTE']).exists()


class TarjetaGuardada(models.Model):
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='tarjeta_guardada'
    )
    nombre_titular = models.CharField(max_length=100)
    ultimos_4_digitos = models.CharField(max_length=4)
    mes_vencimiento = models.PositiveIntegerField()
    ano_vencimiento = models.PositiveIntegerField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # Campo encriptado para almacenar el número de tarjeta de forma segura
    numero_encriptado = models.TextField()
    
    def __str__(self):
        return f"Tarjeta **** **** **** {self.ultimos_4_digitos} de {self.usuario.get_full_name()}"
    
    def save(self, *args, **kwargs):
        # Si no existe la clave de encriptación, generarla
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            # En producción, esto debería estar en variables de entorno
            settings.ENCRYPTION_KEY = Fernet.generate_key()
        
        super().save(*args, **kwargs)
    
    @classmethod
    def crear_tarjeta(cls, usuario, numero_tarjeta, nombre_titular, mes_vencimiento, ano_vencimiento):
        """Crea una nueva tarjeta guardada encriptando el número"""
        # Generar clave de encriptación si no existe
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            settings.ENCRYPTION_KEY = Fernet.generate_key()
        
        cipher = Fernet(settings.ENCRYPTION_KEY)
        numero_encriptado = cipher.encrypt(numero_tarjeta.encode()).decode()
        
        # Eliminar tarjeta anterior si existe
        cls.objects.filter(usuario=usuario).delete()
        
        tarjeta = cls.objects.create(
            usuario=usuario,
            nombre_titular=nombre_titular,
            ultimos_4_digitos=numero_tarjeta[-4:],
            mes_vencimiento=mes_vencimiento,
            ano_vencimiento=ano_vencimiento,
            numero_encriptado=numero_encriptado
        )
        return tarjeta
    
    def obtener_numero_desencriptado(self):
        """Desencripta y retorna el número de tarjeta"""
        if not hasattr(settings, 'ENCRYPTION_KEY'):
            raise ValueError("No se encontró la clave de encriptación")
        
        cipher = Fernet(settings.ENCRYPTION_KEY)
        return cipher.decrypt(self.numero_encriptado.encode()).decode()
    
    @property
    def esta_vencida(self):
        """Verifica si la tarjeta está vencida"""
        from datetime import date
        hoy = date.today()
        fecha_vencimiento = date(self.ano_vencimiento, self.mes_vencimiento, 1)
        return fecha_vencimiento < hoy.replace(day=1)
    
    class Meta:
        verbose_name = "Tarjeta Guardada"
        verbose_name_plural = "Tarjetas Guardadas"
