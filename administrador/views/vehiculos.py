from django.shortcuts import render, redirect
from django.contrib import messages
from vehiculos.models import Vehiculo
from administrador.decorators import admin_required
from django.core.exceptions import ValidationError
from sucursales.models import Sucursal

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
            precio_por_dia = request.POST.get('precio')
            foto_base64 = request.POST.get('foto_base64')
            politica_reembolso = request.POST.get('politica_reembolso')
            sucursal_actual_id = request.POST.get('sucursal')

            # Validaciones
            if not all([marca, modelo, año, patente, precio_por_dia, foto_base64, politica_reembolso, sucursal_actual_id]):
                raise ValidationError("Todos los campos son obligatorios.")

            if Vehiculo.objects.filter(patente=patente).exists():
                raise ValidationError("Ya existe un vehículo con esa patente.")

            # Crear el vehículo
            vehiculo = Vehiculo.objects.create(
                marca=marca,
                modelo=modelo,
                año=int(año),
                patente=patente.upper(),  # Convertir a mayúsculas
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
    if request.method == 'POST':
        patente = request.POST.get('patente')
        
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            vehiculo.delete()
            messages.success(request, "Auto borrado exitosamente")
        except Vehiculo.DoesNotExist:
            messages.error(request, "El auto a borrar no existe")
        except Exception as e:
            messages.error(request, f"Error al borrar el auto: {e}")
            return render(request, 'administrador/borrar_autos.html')
        return redirect('admin_menu')   
    return render(request, 'administrador/borrar_autos.html')


@admin_required
def modificar_autos(request):
    # Obtener todos los vehículos para el selector
    vehiculos = Vehiculo.objects.all().order_by('patente')
    
    # Formatear el precio_por_dia para cada vehículo
    for vehiculo in vehiculos:
        vehiculo.precio_por_dia = f"{float(vehiculo.precio_por_dia):.2f}"
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            
            # Actualizar campos si se proporcionaron
            if marca := request.POST.get('marca'):
                vehiculo.marca = marca
            if modelo := request.POST.get('modelo'):
                vehiculo.modelo = modelo
            if año := request.POST.get('año'):
                vehiculo.año = int(año)
            if precio := request.POST.get('precio'):
                vehiculo.precio_por_dia = precio
            if foto := request.POST.get('foto_base64'):
                vehiculo.foto_base64 = foto
                
            vehiculo.save()
            messages.success(request, "Auto modificado exitosamente")
            return redirect('admin_menu')
            
        except Vehiculo.DoesNotExist:
            messages.error(request, "El auto a modificar no existe")
        except Exception as e:
            messages.error(request, f"Error al modificar el auto: {e}")
    
    return render(request, 'administrador/modificar_autos.html', {'vehiculos': vehiculos}) 

@admin_required
def ver_autos(request):
    vehiculos = Vehiculo.objects.all().order_by('patente')
    return render(request, 'administrador/ver_autos.html', {'vehiculos': vehiculos}) 