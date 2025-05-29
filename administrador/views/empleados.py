from django.shortcuts import render, redirect
from django.contrib import messages
from empleados.models import Empleado
from administrador.decorators import admin_required

@admin_required
def cargar_empleados(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        dni = request.POST.get('dni')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        
        if Empleado.objects.filter(dni=dni).exists():
            messages.error(request, "Ya existe un empleado con ese DNI.")
            return render(request, 'administrador/cargar_empleados.html')
            
        try:
            Empleado.objects.create(
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                email=email,
                telefono=telefono
            )
            messages.success(request, "Empleado cargado exitosamente")
            return redirect('admin_menu')
        except Exception as e:
            messages.error(request, f"Error al cargar el empleado: {e}")
            
    return render(request, 'administrador/cargar_empleados.html') 