from django.db import models
from django.conf import settings 
from vehiculos.models import Vehiculo
import datetime
from decimal import Decimal

class Reserva(models.Model):
    ESTADO_RESERVA_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('RETIRADO', 'Retirado'),
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
    costo_total = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,
        blank=True,
        help_text="Costo total de la reserva incluyendo adicionales."
    )
    costo_base = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True,
        blank=True,
        help_text="Costo base de la reserva sin adicionales."
    )
    monto_adicional = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Monto total de los adicionales."
    )
    estado = models.CharField(max_length=20, choices=ESTADO_RESERVA_CHOICES, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    monto_a_reembolsar = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=Decimal('0.00'),
    blank=True,
    null=True,
    help_text="Monto calculado a reembolsar en caso de cancelación."
    )

        # Campos del conductor
    conductor_nombre = models.CharField(max_length=100, null=True, blank=True)
    conductor_apellido = models.CharField(max_length=100, null=True, blank=True)
    conductor_dni = models.CharField(max_length=20, null=True, blank=True, unique=True)
    
    # Campos para extras
    silla_para_ninos = models.BooleanField(default=False)
    telepass = models.BooleanField(default=False)
    seguro_por_danos = models.BooleanField(default=False)
    conductor_adicional = models.BooleanField(default=False)
    
    # Campos para conductor adicional
    conductor_adicional_nombre = models.CharField(max_length=100, null=True, blank=True)
    conductor_adicional_apellido = models.CharField(max_length=100, null=True, blank=True)
    conductor_adicional_dni = models.CharField(max_length=20, null=True, blank=True)
    
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

        # Validar que el conductor adicional no esté en otra reserva en el mismo período
        if self.conductor_adicional and self.conductor_adicional_dni:
            reservas_solapadas = Reserva.objects.filter(
                conductor_adicional_dni=self.conductor_adicional_dni,
                fecha_recogida__lt=self.fecha_devolucion,
                fecha_devolucion__gt=self.fecha_recogida,
                estado__in=['PENDIENTE', 'CONFIRMADA']
            )
            if self.pk:  # Si es una actualización, excluir la reserva actual
                reservas_solapadas = reservas_solapadas.exclude(pk=self.pk)
            if reservas_solapadas.exists():
                raise ValidationError({'conductor_adicional_dni': "Ya existe una reserva con este conductor adicional en el período seleccionado."})

    def save(self, *args, **kwargs):
        # Lógica para calcular costo_base
        if self.fecha_recogida and self.fecha_devolucion and self.vehiculo.precio_por_dia:
            dias = (self.fecha_devolucion - self.fecha_recogida).days
            if dias > 0:
                self.costo_base = self.vehiculo.precio_por_dia * dias
            else:
                self.costo_base = self.vehiculo.precio_por_dia

        # Calcular extras
        extras_total = Decimal('0.00')
        if self.silla_para_ninos:
            extras_total += Decimal('1000.00') * dias
        if self.telepass:
            extras_total += Decimal('2000.00') * dias
        if self.seguro_por_danos:
            extras_total += self.costo_base * Decimal('0.30')
        if self.conductor_adicional:
            extras_total += self.costo_base * Decimal('0.20')

        # Actualizar monto_adicional y costo_total
        self.monto_adicional = extras_total
        self.costo_total = self.costo_base + extras_total

        if self.estado == 'CANCELADA' and self.costo_total is not None:
            if hasattr(self.vehiculo, 'politica_de_reembolso') and self.vehiculo.politica_de_reembolso is not None:
                politica_porcentaje = Decimal(str(self.vehiculo.politica_de_reembolso))
                self.monto_a_reembolsar = (self.costo_total * politica_porcentaje) / Decimal('100.00')
            else:
                self.monto_a_reembolsar = Decimal('0.00')
        elif self.estado != 'CANCELADA':
            self.monto_a_reembolsar = Decimal('0.00')

        super().save(*args, **kwargs)


    def __str__(self):
        return f"Reserva {self.id} de {self.cliente.get_full_name() or self.cliente.email} para {self.vehiculo}"

    class Meta:
        verbose_name_plural = "Reservas"
        ordering = ['fecha_recogida'] 
