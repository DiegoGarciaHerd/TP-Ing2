from django.db import models
from sucursales.models import Sucursal
from decimal import Decimal

class Vehiculo(models.Model):
    TIPO_CHOICES = [
        ('AUTOMOVIL', 'Automóvil'),
        ('CAMIONETA', 'Camioneta'),
        ('4X4', '4x4'),
    ]

    REEMBOLSO_CHOICES = [
        ('0', '0%'),
        ('20', '20%'),
        ('100', '100%'),
    ]

    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    año = models.PositiveIntegerField()
    patente = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='AUTOMOVIL')
    capacidad = models.PositiveIntegerField(default=5, help_text='Número de pasajeros')
    precio_por_dia = models.DecimalField(max_digits=10, decimal_places=2)
    sucursal_actual = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='vehiculos_en_sucursal')
    disponible = models.BooleanField(default=True)
    foto_base64 = models.TextField(blank=True, null=True)
    politica_de_reembolso = models.CharField(
        max_length=3,
        choices=REEMBOLSO_CHOICES,
        default='0'
    )
    precio_por_dia = models.DecimalField(
        max_digits=10,        # Ej. hasta $9,999,999.99
        decimal_places=2,     # Dos decimales para los centavos
        default=Decimal('0.00'), # Valor por defecto
        help_text="Precio de alquiler por día."
    )
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente})"

    class Meta:
        verbose_name_plural = "Vehículos"