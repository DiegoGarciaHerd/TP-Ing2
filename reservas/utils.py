from .models import Reserva
from datetime import timedelta

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