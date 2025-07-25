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
            kilometraje = request.POST.get('kilometraje', 0)  # Valor por defecto si no se proporciona
            

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
                #disponible=True,
                estado='DISPONIBLE',
                sucursal_actual_id=sucursal_actual_id,  # TODO: Permitir seleccionar sucursal
                foto_base64=foto_base64,
                politica_de_reembolso=politica_reembolso,
                kilometraje=int(kilometraje) if kilometraje.isdigit() else 0,  # Validar que sea un número
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
    vehiculos = Vehiculo.objects.exclude(estado='BAJA').order_by('patente')
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            vehiculo.estado = 'BAJA'  # Cambiar a estado BAJA en lugar de disponible=False
            vehiculo.save()
            
            messages.success(request, f"Vehículo {vehiculo.marca} {vehiculo.modelo} dado de baja exitosamente")
            return redirect('admin_menu')
            
        except Vehiculo.DoesNotExist:
            messages.error(request, "El vehículo no existe")
        except Exception as e:
            messages.error(request, f"Error al dar de baja el vehículo: {str(e)}")
    
    return render(request, 'administrador/borrar_autos.html', {
        'vehiculos': vehiculos
    })

@admin_required
def modificar_autos(request):
    vehiculos = Vehiculo.objects.all().order_by('patente')
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            
            # Actualizar campos
            if precio := request.POST.get('precio'):
                vehiculo.precio_por_dia = precio
            if foto := request.POST.get('foto_base64'):
                vehiculo.foto_base64 = foto
            if politica_reembolso := request.POST.get('politica_reembolso'):
                vehiculo.politica_de_reembolso = politica_reembolso
            if estado := request.POST.get('estado'):  # Nuevo campo estado
                vehiculo.estado = estado
            if kilometraje := request.POST.get('kilometraje'):
                vehiculo.kilometraje = kilometraje
                
            vehiculo.save()
            messages.success(request, "Vehículo modificado exitosamente")
            return redirect('admin_menu')
            
        except Vehiculo.DoesNotExist:
            messages.error(request, "El vehículo no existe")
        except Exception as e:
            messages.error(request, f"Error al modificar el vehículo: {str(e)}")
    
    return render(request, 'administrador/modificar_autos.html', {
        'vehiculos': vehiculos,
        'estados': Vehiculo.ESTADO_CHOICES  # Pasar opciones de estado al template
    })

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
                'kilometraje': vehiculo.kilometraje,
                'estado': vehiculo.estado
            }
            return JsonResponse(data)
        except Vehiculo.DoesNotExist:
            return JsonResponse({'error': 'Vehículo no encontrado'}, status=404)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

 
@admin_required
def gestionar_vehiculos(request):
    vehiculos = Vehiculo.objects.all().order_by('estado', 'patente')
    

    estado_filtro = request.GET.get('estado')
    if estado_filtro:
        vehiculos = vehiculos.filter(estado=estado_filtro)
    
    if request.method == 'POST':
        vehiculo_id = request.POST.get('vehiculo_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        
        try:
            vehiculo = Vehiculo.objects.get(id=vehiculo_id)
            vehiculo.estado = nuevo_estado
            vehiculo.save()
            messages.success(request, f"Estado actualizado: {vehiculo.patente} → {vehiculo.get_estado_display()}")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('gestionar_vehiculos')
    
    return render(request, 'administrador/gestion_vehiculos.html', {
        'vehiculos': vehiculos,
        'estados': Vehiculo.ESTADO_CHOICES,
        'estado_filtro': estado_filtro
    })