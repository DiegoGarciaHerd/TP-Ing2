from django.db import models

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.nombre} - {self.direccion}"

    class Meta:
        verbose_name_plural = "Sucursales"


class Vehiculo(models.Model):

    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    año = models.PositiveIntegerField()
    patente = models.CharField(max_length=10, unique=True)
    precio_por_dia = models.DecimalField(max_digits=10, decimal_places=2)
    sucursal_actual = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='vehiculos')
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente})"

    class Meta:
        verbose_name_plural = "Vehículos"
