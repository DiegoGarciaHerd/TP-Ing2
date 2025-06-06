from .models import Reserva
from datetime import timedelta
from django.utils import timezone
import uuid
import random
import time

def validar_reserva(usuario, vehiculo, conductor_dni, fecha_inicio, fecha_fin):
    if fecha_fin <= fecha_inicio:
        return False, "El alquiler debe ser de al menos un día completo."

    if (fecha_fin - fecha_inicio).days > 30:
        return False, "Las fechas seleccionadas deben estar dentro del límite permitido para alquiler (1 mes)."

    if Reserva.objects.filter(
        usuario=usuario,
        fecha_inicio__lt=fecha_fin,
        fecha_fin__gt=fecha_inicio
    ).exists():
        return False, "No puedes realizar una nueva reserva que se superponga con una reserva existente."

    if Reserva.objects.filter(
        vehiculo=vehiculo,
        fecha_inicio__lt=fecha_fin,
        fecha_fin__gt=fecha_inicio
    ).exists():
        return False, "El vehículo seleccionado no está disponible en las fechas indicadas."

    if Reserva.objects.filter(
        conductor_dni=conductor_dni,
        fecha_inicio__lt=fecha_fin,
        fecha_fin__gt=fecha_inicio
    ).exists():
        return False, "El conductor seleccionado ya está asignado a otra reserva en estas fechas."

    return True, None

def calcular_costo_total(vehiculo, fecha_recogida, fecha_devolucion):
    """
    Calcula el costo total de una reserva.
    """
    dias = (fecha_devolucion - fecha_recogida).days
    if dias > 0:
        return dias * vehiculo.precio_por_dia
    else:
        return vehiculo.precio_por_dia


def procesar_pago_tarjeta(numero_tarjeta, nombre_titular, mes_vencimiento, ano_vencimiento, cvv, monto):
    """
    Simula el procesamiento de un pago con tarjeta de crédito.
    En un sistema real, esto se conectaría con un procesador de pagos como Stripe, PayPal, etc.
    
    Returns:
        dict: Resultado del procesamiento con éxito/error y datos del pago
    """
    
    # Simular delay de procesamiento
    time.sleep(2)
    
    # Simular una tasa de éxito del 95% (para demostración)
    exito = random.random() > 0.05
    
    if exito:
        # Generar una referencia de pago única
        referencia_pago = f"PAY_{uuid.uuid4().hex[:8].upper()}"
        
        # Obtener últimos 4 dígitos
        ultimos_4_digitos = numero_tarjeta[-4:]
        
        return {
            'exito': True,
            'referencia_pago': referencia_pago,
            'ultimos_4_digitos': ultimos_4_digitos,
            'fecha_procesamiento': timezone.now(),
            'monto_procesado': monto,
            'mensaje': 'Pago procesado exitosamente'
        }
    else:
        # Simular diferentes tipos de errores
        errores = [
            'Fondos insuficientes',
            'Tarjeta rechazada por el banco',
            'Error de comunicación con el banco',
            'Transacción sospechosa detectada'
        ]
        
        return {
            'exito': False,
            'codigo_error': f"ERR_{random.randint(1000, 9999)}",
            'mensaje': random.choice(errores),
            'fecha_procesamiento': timezone.now()
        }