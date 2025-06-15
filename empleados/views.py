from django.shortcuts import render

# Create your views here.
def menu_empleado(request):
    return render(request, 'empleados/menu_empleados.html')

def login_empleado(request):
    return render(request, 'empleados/login_empleado.html')

def buscar_cliente(request):
    return render(request, 'empleados/buscar_cliente.html')

def modificar_vehiculo(request):
    return render(request, 'empleados/modificar_vehiculo.html')

def reserva_empleado(request):
    return render(request, 'empleados/reserva_empleado.html')