from django.db import models
from django.conf import settings # Para importar el modelo de usuario personalizado
from sucursales.models import Vehiculo # Importar el modelo Vehiculo
import datetime

class Reserva(models.Model):
    ESTADO_RESERVA_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    )

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='reservas')
    fecha_recogida = models.DateField()
    fecha_devolucion = models.DateField()
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_RESERVA_CHOICES, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def clean(self):

        if self.fecha_recogida and self.fecha_recogida < datetime.date.today():
            from django.core.exceptions import ValidationError
            raise ValidationError({'fecha_recogida': "La fecha de recogida no puede ser anterior a la fecha actual."})

        if self.fecha_recogida and self.fecha_devolucion and self.fecha_devolucion < self.fecha_recogida:
            from django.core.exceptions import ValidationError
            raise ValidationError({'fecha_devolucion': "La fecha de devolución no puede ser anterior a la fecha de recogida."})

    def save(self, *args, **kwargs):

        if not self.costo_total and self.fecha_recogida and self.fecha_devolucion and self.vehiculo:
            delta = self.fecha_devolucion - self.fecha_recogida
            self.costo_total = delta.days * self.vehiculo.precio_por_dia
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva {self.id} de {self.cliente.get_full_name() or self.cliente.email} para {self.vehiculo}"

    class Meta:
        verbose_name_plural = "Reservas"
        ordering = ['fecha_recogida'] 
