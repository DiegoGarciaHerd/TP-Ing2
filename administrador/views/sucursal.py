# D:\Tp IS2\TP-Ing2\administrador\views\sucursal.py
import random
import string
from django.shortcuts import render, redirect
from django.contrib import messages
from administrador.decorators import admin_required
from django.conf import settings
from sucursales.models import Sucursal

@admin_required
def cargar_sucursal(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            direccion = request.POST.get('direccion')
            telefono = request.POST.get('telefono')

            if Sucursal.objects.filter(nombre=nombre).exists():
                messages.error(request, "Ya existe una sucursal con ese nombre.")
                return render(request, 'administrador/cargar_sucursal.html')
            
            sucursal = Sucursal.objects.create(
                nombre=nombre,
                direccion=direccion,
                telefono=telefono
            )
            messages.success(request, 'Sucursal {sucursal.nombre} cargada exitosamente.')
            return redirect('admin_menu')
        except Exception as e:
            messages.error(request, f"Error al cargar la sucursal: {str(e)}")
            return render(request, 'administrador/cargar_sucursal.html')

    return render(request, 'administrador/cargar_sucursal.html')

@admin_required
def modificar_sucursal(request):

    return render(request, 'administrador/modificar_sucursal.html')

@admin_required
def borrar_sucursal(request):
    if request.method == 'POST':
        nombreSucursal = request.POST.get('nombreChau')
        try:
            sucursal = Sucursal.objects.get(nombre=nombreSucursal)
            sucursal.delete()
            messages.success(request, 'Sucursal eliminada exitosamente.')
            return redirect('admin_menu')
        except Sucursal.DoesNotExist:
            messages.error(request, "La sucursal no existe o fue borrada previamente.")
        except Exception as e:
            messages.error(request, f"Error al eliminar la sucursal: {str(e)}")
        return redirect('admin_menu')
    return render(request, 'administrador/borrar_sucursal.html')