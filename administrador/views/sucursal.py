# D:\Tp IS2\TP-Ing2\administrador\views\sucursal.py
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from administrador.decorators import admin_required
from django.conf import settings
from sucursales.models import Sucursal
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone # Importa timezone

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
            messages.success(request, f'Sucursal {sucursal.nombre} cargada exitosamente.')
            return redirect('admin_menu')
        except Exception as e:
            messages.error(request, f"Error al cargar la sucursal: {str(e)}")
            return render(request, 'administrador/cargar_sucursal.html')

    return render(request, 'administrador/cargar_sucursal.html')

@admin_required
def modificar_sucursal(request):
    # Obtener todas las sucursales para pasarlas al selector en la plantilla
    sucursales = Sucursal.objects.all().order_by('nombre')

    if request.method == 'POST':
        nombre_sucursal_seleccionada = request.POST.get('nombre_sucursal_selector')
        nueva_direccion = request.POST.get('direccion')
        nuevo_telefono = request.POST.get('telefono')

        if not nombre_sucursal_seleccionada:
            messages.error(request, "Por favor, seleccione una sucursal para modificar.")
            # Si hay un error, volvemos a renderizar la página pasando las sucursales
            return render(request, 'administrador/modificar_sucursal.html', {'sucursales': sucursales})

        try:
            # Intentar obtener la sucursal por su nombre
            sucursal = get_object_or_404(Sucursal, nombre=nombre_sucursal_seleccionada)

            # Actualizar los campos si se proporcionaron nuevos valores
            # Se usa 'if nueva_direccion' para que no se actualice si el campo está vacío
            if nueva_direccion:
                sucursal.direccion = nueva_direccion
            if nuevo_telefono:
                sucursal.telefono = nuevo_telefono
            
            sucursal.save() # Guardar los cambios en la base de datos
            messages.success(request, f"Sucursal '{sucursal.nombre}' modificada exitosamente.")
            return redirect('modificar_sucursal') # Redirigir para limpiar el formulario y mostrar el mensaje

        except Exception as e:
            messages.error(request, f"Error al modificar la sucursal: {str(e)}")
            # Si hay un error, volvemos a renderizar la página pasando las sucursales
            return render(request, 'administrador/modificar_sucursal.html', {'sucursales': sucursales})

    # Renderizar la plantilla por primera vez (método GET) o si hay errores
    return render(request, 'administrador/modificar_sucursal.html', {'sucursales': sucursales})

@admin_required
def obtener_datos_sucursal(request):
    """
    Vista AJAX para obtener los datos de una sucursal por su nombre.
    """
    nombre_sucursal = request.GET.get('nombre', None)
    if nombre_sucursal:
        try:
            sucursal = Sucursal.objects.get(nombre=nombre_sucursal)
            data = {
                'direccion': sucursal.direccion,
                'telefono': sucursal.telefono,
                # Puedes añadir más campos aquí si los necesitas en el futuro
            }
            return JsonResponse(data)
        except Sucursal.DoesNotExist:
            return JsonResponse({'error': 'Sucursal no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Parámetro de nombre de sucursal no proporcionado'}, status=400)

@admin_required
def borrar_sucursal(request):
    if request.method == 'POST':
        nombre_sucursal = request.POST.get('nombre') # Obtiene el nombre desde el formulario
        try:
            sucursal = get_object_or_404(Sucursal, nombre=nombre_sucursal)
            sucursal.soft_delete()  # Usa el método soft_delete
            messages.success(request, f"La sucursal '{sucursal.nombre}' ha sido dada de baja exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al dar de baja la sucursal: {str(e)}")
        return redirect('listado_sucursales') # Redirige al listado
    return redirect('listado_sucursales') # Si no es POST, redirige también

@admin_required
def listado_sucursales(request):
    mostrar_inactivas = request.GET.get('mostrar_inactivas') == 'on'

    if mostrar_inactivas:
        sucursales_list = Sucursal.objects.all().order_by('nombre')
    else:
        sucursales_list = Sucursal.objects.filter(activo=True).order_by('nombre')

    paginator = Paginator(sucursales_list, 10) # 10 sucursales por página
    page = request.GET.get('page')

    try:
        sucursales = paginator.page(page)
    except PageNotAnInteger:
        sucursales = paginator.page(1)
    except EmptyPage:
        sucursales = paginator.page(paginator.num_pages)

    context = {
        'sucursales': sucursales,
        'is_paginated': sucursales.has_other_pages,
        'page_obj': sucursales,
        'mostrar_inactivas': mostrar_inactivas,
    }
    return render(request, 'administrador/listado_sucursales.html', context)