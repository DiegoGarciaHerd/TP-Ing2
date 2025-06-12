from django.db import models
from django.conf import settings 
from vehiculos.models import Vehiculo
import datetime

class Reserva(models.Model):
    ESTADO_RESERVA_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    )

    ESTADO_PAGO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PROCESANDO', 'Procesando'),
        ('PAGADO', 'Pagado'),
        ('FALLIDO', 'Fallido'),
        ('REEMBOLSADO', 'Reembolsado'),
    )

    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name='reservas')
    fecha_recogida = models.DateField()
    fecha_devolucion = models.DateField()
    costo_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_RESERVA_CHOICES, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Campos del conductor
    conductor_nombre = models.CharField(max_length=100, null=True, blank=True)
    conductor_apellido = models.CharField(max_length=100, null=True, blank=True)
    conductor_dni = models.CharField(max_length=20, null=True, blank=True, unique=True)
    
    # Campos de pago
    estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='PENDIENTE')
    fecha_pago = models.DateTimeField(null=True, blank=True)
    referencia_pago = models.CharField(max_length=100, null=True, blank=True)
    ultimos_4_digitos_tarjeta = models.CharField(max_length=4, null=True, blank=True)

    def clean(self):
        if self.fecha_recogida and self.fecha_recogida < datetime.date.today():
            from django.core.exceptions import ValidationError
            raise ValidationError({'fecha_recogida': "La fecha de recogida no puede ser anterior a la fecha actual."})

        if self.fecha_recogida and self.fecha_devolucion and self.fecha_devolucion < self.fecha_recogida:
            from django.core.exceptions import ValidationError
            raise ValidationError({'fecha_devolucion': "La fecha de devolución no puede ser anterior a la fecha de recogida."})

        # Validar que el DNI del conductor no esté en uso en otra reserva activa
        if self.conductor_dni and self.conductor_dni.strip():  # Verificar que no sea None ni vacío
            reservas_existentes = Reserva.objects.filter(
                conductor_dni=self.conductor_dni,
                fecha_recogida__lt=self.fecha_devolucion,
                fecha_devolucion__gt=self.fecha_recogida,
                estado__in=['PENDIENTE', 'CONFIRMADA']
            ).exclude(id=self.id)  # Excluir la reserva actual en caso de actualización

            if reservas_existentes.exists():
                raise ValidationError({
                    'conductor_dni': "Este DNI ya está asignado a otra reserva activa en las fechas seleccionadas."
                })

    def save(self, *args, **kwargs):
        if self.fecha_recogida and self.fecha_devolucion and self.vehiculo.precio_por_dia:
            dias = (self.fecha_devolucion - self.fecha_recogida).days
            if dias > 0:
                self.costo_total = self.vehiculo.precio_por_dia * dias
            else:
                self.costo_total = self.vehiculo.precio_por_dia
        super().save(*args, **kwargs)

    @property
    def esta_pagado(self):
        return self.estado_pago == 'PAGADO'

    def __str__(self):
        return f"Reserva {self.id} de {self.cliente.get_full_name() or self.cliente.email} para {self.vehiculo}"

    class Meta:
        verbose_name_plural = "Reservas"
        ordering = ['fecha_recogida'] 
