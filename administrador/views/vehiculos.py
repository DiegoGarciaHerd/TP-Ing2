from datetime import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from vehiculos.models import Vehiculo
from administrador.decorators import admin_required
from django.core.exceptions import ValidationError
from sucursales.models import Sucursal
from django.http import JsonResponse
from reservas.models import Reserva

@admin_required
def cargar_autos(request):
    sucursales = Sucursal.objects.all()
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            marca = request.POST.get('marca')
            modelo = request.POST.get('modelo')
            año = request.POST.get('año')
            patente = request.POST.get('patente')
            tipo = request.POST.get('tipo')
            capacidad = request.POST.get('capacidad')
            precio_por_dia = request.POST.get('precio')
            foto_base64 = request.POST.get('foto_base64')
            politica_reembolso = request.POST.get('politica_reembolso')
            sucursal_actual_id = request.POST.get('sucursal')

            # Validaciones
            if not all([marca, modelo, año, patente, tipo, capacidad, precio_por_dia, foto_base64, politica_reembolso, sucursal_actual_id]):
                raise ValidationError("Todos los campos son obligatorios.")

            if Vehiculo.objects.filter(patente=patente).exists():
                raise ValidationError("Ya existe un vehículo con esa patente.")

            # Crear el vehículo
            vehiculo = Vehiculo.objects.create(
                marca=marca,
                modelo=modelo,
                año=int(año),
                patente=patente.upper(),  # Convertir a mayúsculas
                tipo=tipo,
                capacidad=int(capacidad),
                precio_por_dia=precio_por_dia,
                disponible=True,
                sucursal_actual_id=sucursal_actual_id,  # TODO: Permitir seleccionar sucursal
                foto_base64=foto_base64,
                politica_de_reembolso=politica_reembolso
            )
            
            messages.success(request, f"Vehículo {vehiculo.marca} {vehiculo.modelo} cargado exitosamente")
            return redirect('admin_menu')

        except ValidationError as e:
            messages.error(request, str(e))
        except ValueError as e:
            messages.error(request, "Error en el formato de los datos ingresados")
        except Exception as e:
            messages.error(request, f"Error al cargar el vehículo: {str(e)}")
    
    return render(request, 'administrador/cargar_autos.html', {'sucursales': sucursales})

@admin_required
def borrar_autos(request):
    # Obtener todos los vehículos para el selector
    vehiculos = Vehiculo.objects.all().order_by('patente')
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            vehiculo.disponible = False
            vehiculo.save()
            messages.success(request, f"El vehículo {vehiculo.marca} {vehiculo.modelo} ha sido marcado como no disponible y removido del catálogo.")
        except Vehiculo.DoesNotExist:
            messages.error(request, "El vehículo a borrar no existe")
        except Exception as e:
            messages.error(request, f"Error al procesar el vehículo: {e}")
            return render(request, 'administrador/borrar_autos.html', {'vehiculos': vehiculos})
        return redirect('admin_menu')   
    return render(request, 'administrador/borrar_autos.html', {'vehiculos': vehiculos})


@admin_required
def modificar_autos(request):
    # Obtener todos los vehículos para el selector
    vehiculos = Vehiculo.objects.all().order_by('patente')
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            
            # Actualizar campos si se proporcionaron
            if precio := request.POST.get('precio'):
                vehiculo.precio_por_dia = precio
            if foto := request.POST.get('foto_base64'):
                vehiculo.foto_base64 = foto
            if (politica_reembolso := request.POST.get('politica_reembolso')):
                vehiculo.politica_de_reembolso = politica_reembolso
                
            vehiculo.save()
            messages.success(request, "Auto modificado exitosamente")
            return redirect('admin_menu')
            
        except Vehiculo.DoesNotExist:
            messages.error(request, "El auto a modificar no existe")
        except Exception as e:
            messages.error(request, f"Error al modificar el auto: {e}")
    
    return render(request, 'administrador/modificar_autos.html', {'vehiculos': vehiculos})

@admin_required
def obtener_datos_vehiculo(request):
    """Vista para obtener los datos de un vehículo específico vía AJAX"""
    if request.method == 'GET':
        patente = request.GET.get('patente')
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            data = {
                'marca': vehiculo.marca,
                'modelo': vehiculo.modelo,
                'año': vehiculo.año,
                'tipo': vehiculo.get_tipo_display(),
                'capacidad': vehiculo.capacidad,
                'precio_por_dia': str(vehiculo.precio_por_dia),
                'politica_de_reembolso': vehiculo.politica_de_reembolso,
                'foto_base64': vehiculo.foto_base64,
                'sucursal': vehiculo.sucursal_actual.nombre,
                'disponible': vehiculo.disponible
            }
            return JsonResponse(data)
        except Vehiculo.DoesNotExist:
            return JsonResponse({'error': 'Vehículo no encontrado'}, status=404)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@admin_required
def ver_autos(request):
    # Obtener todos los vehículos
    queryset = Vehiculo.objects.all().select_related('sucursal_actual').order_by('patente')
    
    # Aplicar filtros
    sucursal = request.GET.get('sucursal')
    estado = request.GET.get('estado')
    
    if sucursal:
        queryset = queryset.filter(sucursal_actual_id=sucursal)
    if estado:
        if estado == 'disponible':
            queryset = queryset.filter(disponible=True)
        elif estado == 'no_disponible':
            queryset = queryset.filter(disponible=False)
    
    context = {
        'vehiculos': queryset,
        'sucursales': Sucursal.objects.all(),
        'sucursal_seleccionada': sucursal,
        'estado_seleccionado': estado
    }
    return render(request, 'administrador/ver_autos.html', context)

@admin_required
def toggle_disponibilidad(request, vehiculo_id):
    """Vista para dar de baja o reactivar un vehículo"""
    if request.method == 'POST':
        vehiculo = get_object_or_404(Vehiculo, id=vehiculo_id)
        vehiculo.disponible = not vehiculo.disponible
        vehiculo.save()
        
        mensaje = "Vehículo reactivado en el catálogo" if vehiculo.disponible else "Vehículo dado de baja del catálogo"
        messages.success(request, mensaje)
        
        return redirect('ver_autos')
    
    return redirect('ver_autos') 