from django.db import models
from django.utils import timezone

class Sucursal(models.Model):
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)

    activo = models.BooleanField(default=True)
    fecha_baja = models.DateTimeField(null=True, blank=True)

    def soft_delete(self):
        self.activo = False
        self.fecha_baja = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.nombre} - {self.direccion}"

    class Meta:
        verbose_name_plural = "Sucursales"


