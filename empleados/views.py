# ... (tus importaciones existentes)
from django.contrib import messages
from django.contrib.auth import authenticate, login
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
def reserva_empleado(request):
    return render(request, 'empleados/reserva_empleado.html')


def login_empleado(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        usuario = authenticate(request, username=username, password=password)
        if usuario is not None:
            login(request, usuario)
            messages.success(request, "Inicio de sesión exitoso.")
            return redirect('empleados:menu_empleado')
        else:
            messages.error(request, "Credenciales inválidas. Por favor, inténtalo de nuevo.")

    return render(request, 'empleados/login_empleado.html')

def modificar_autos(request):
    # Obtener todos los vehículos para el selector
    vehiculos = Vehiculo.objects.all().order_by('patente')
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            
            # Actualizar campos si se proporcionaron
            if kilometraje := request.POST.get('kilometraje'):
                vehiculo.kilometraje = kilometraje
            if (disponibilidad := request.POST.get('disponibilidad')):
                vehiculo.disponibilidad = disponibilidad
                
            vehiculo.save()
            messages.success(request, "Auto modificado exitosamente")
            return redirect('empleados:menu_empleado')
            
        except Vehiculo.DoesNotExist:
            messages.error(request, "El auto a modificar no existe")
        except Exception as e:
            messages.error(request, f"Error al modificar el auto: {e}")
    
    return render(request, 'empleados/modificar_autos.html', {'vehiculos': vehiculos})
