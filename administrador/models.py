from django.db import models

# Create your models here.
class Vehiculo(models.Model):
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.IntegerField()
    patente = models.CharField(max_length=10, unique=True)
    precio_por_dia = models.DecimalField(max_digits=10, decimal_places=2)
    disponible = models.BooleanField(default=True)
    sucursal_actual_id = models.IntegerField()

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente}) ({self.disponible})"