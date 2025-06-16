from pyexpat.errors import messages
from django.core.exceptions import ValidationError
from django.shortcuts import render
from vehiculos.models import Vehiculo
from django.contrib import messages

# Create your views here.
def menu_empleado(request):
    return render(request, 'empleados/menu_empleado.html')

def login_empleado(request):
    return render(request, 'empleados/login_empleado.html')

def buscar_cliente(request):
    return render(request, 'empleados/buscar_cliente.html')

def modificar_vehiculo(request):
    vehiculos = Vehiculo.objects.all().order_by('patente')

    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
           vehiculo = Vehiculo.objects.get(patente=patente)
           
           if kilometraje := request.POST.get('kilometraje'):
               vehiculo.kilometraje = kilometraje
           if disponibilidad := request.POST.get('disponibilidad'):
               vehiculo.disponible = disponibilidad

        except Vehiculo.DoesNotExist:
            messages.error(request, "El vehículo no existe")
        except Exception as e:
            messages.error(request, "Ocurrió un error al buscar el vehículo: " + str(e))        

    return render(request, 'empleados/modificar_vehiculo.html', {'vehiculos': vehiculos})

def reserva_empleado(request):
    return render(request, 'empleados/reserva_empleado.html')