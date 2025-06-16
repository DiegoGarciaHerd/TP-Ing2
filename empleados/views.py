# ... (tus importaciones existentes)
from django.contrib import messages
from django.shortcuts import render, redirect
from django.urls import reverse
from vehiculos.models import Vehiculo
from .decorators import empleado_required # <-- IMPORTA EL DECORADOR

# La vista menu_empleado
@empleado_required # Aplica el decorador aquí
def menu_empleado(request):
    return render(request, 'empleados/menu_empleado.html')

# Las otras vistas de empleado también deberían ser protegidas
@empleado_required
def buscar_cliente(request):
    return render(request, 'empleados/buscar_cliente.html')

@empleado_required
def modificar_vehiculo(request):
    vehiculos = Vehiculo.objects.all().order_by('patente')

    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
           vehiculo = Vehiculo.objects.get(patente=patente)
           
           if kilometraje := request.POST.get('kilometraje'):
               vehiculo.kilometraje = int(kilometraje)
           if disponibilidad := request.POST.get('disponibilidad'):
               vehiculo.disponible = disponibilidad

        except Vehiculo.DoesNotExist:
            messages.error(request, "El vehículo no existe.")
        except ValueError:
            messages.error(request, "Kilometraje debe ser un número válido.")
        except Exception as e:
            messages.error(request, "Ocurrió un error al modificar el vehículo: " + str(e))     

    return render(request, 'empleados/modificar_vehiculo.html', {'vehiculos': vehiculos})

@empleado_required
def reserva_empleado(request):
    return render(request, 'empleados/reserva_empleado.html')


def login_empleado(request):

    return render(request, 'empleados/login_empleado.html')