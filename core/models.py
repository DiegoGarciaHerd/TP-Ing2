from django.db import models
from decimal import Decimal # Importa Decimal para mayor precisión

class AdminBalance(models.Model):
    """
    Modelo para almacenar el saldo total acumulado de las reservas
    del sistema. Está diseñado para tener una única instancia.
    """
    saldo = models.DecimalField(
        max_digits=10,       # Total de dígitos, ej. 999.999.999.999,99
        decimal_places=2,    # Dos decimales para moneda
        default=Decimal('0.00'), # Usar Decimal para el default
        help_text="Saldo total acumulado por el sistema de alquileres."
    )
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Saldo del Administrador"
        verbose_name_plural = "Saldos del Administrador"

    def __str__(self):
        return f"Balance: ${self.saldo}"

    # Método para asegurar que solo haya una instancia
    def save(self, *args, **kwargs):
        if not self.pk and AdminBalance.objects.exists():
            # Si ya existe una instancia, no permitir crear otra.
            # Puedes levantar una excepción o manejarlo de otra forma.
            raise Exception("Solo puede existir una instancia de AdminBalance.")
        super().save(*args, **kwargs)

class EncryptionKey(models.Model):
    key = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Clave de Encriptación"
        verbose_name_plural = "Claves de Encriptación"
    
    def __str__(self):
        return f"Clave de encriptación (creada: {self.created_at})"