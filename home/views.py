from django.shortcuts import render, redirect
from sucursales.models import Sucursal
from vehiculos.models import Vehiculo
from reservas.models import Reserva
from datetime import datetime

# Create your views here.

def home(request):
    sucursales = Sucursal.objects.all()
    return render(request, 'home/home.html', {'sucursales': sucursales})

def contacto(request):
    return render(request, 'home/contacto.html')

def buscar_vehiculos(request):
    # Obtener todas las sucursales para el formulario
    sucursales = Sucursal.objects.all()
    
    if request.method == 'POST':
        try:
            sucursal_retiro_id = request.POST.get('sucursal_retiro')
            sucursal_devolucion_id = request.POST.get('sucursal_devolucion')
            fecha_retiro = request.POST.get('fecha_retiro')
            fecha_entrega = request.POST.get('fecha_entrega')
            misma_sucursal = request.POST.get('misma_sucursal') == 'on'
            
            if not all([sucursal_retiro_id, fecha_retiro, fecha_entrega]):
                return render(request, 'home/buscar_vehiculos.html', {
                    'sucursales': sucursales,
                    'error': 'Por favor complete todos los campos',
                    'fecha_retiro': fecha_retiro,
                    'fecha_entrega': fecha_entrega,
                    'sucursal_seleccionada': sucursal_retiro_id,
                    'misma_sucursal': misma_sucursal
                })
            
            # Convertir las fechas a objetos datetime
            fecha_retiro = datetime.strptime(fecha_retiro, '%Y-%m-%d').date()
            fecha_entrega = datetime.strptime(fecha_entrega, '%Y-%m-%d').date()
            
            # Si es la misma sucursal, usar la sucursal de retiro para la devolución
            if misma_sucursal:
                sucursal_devolucion_id = sucursal_retiro_id
            
            # Obtener vehículos disponibles en la sucursal de retiro
            vehiculos_base = Vehiculo.objects.filter(
                sucursal_actual_id=sucursal_retiro_id,
                disponible=True
            )
            
            # Filtrar vehículos que no tienen reservas en el período seleccionado
            vehiculos_disponibles = []
            for vehiculo in vehiculos_base:
                reservas_existentes = Reserva.objects.filter(
                    vehiculo=vehiculo,
                    fecha_recogida__lt=fecha_entrega,
                    fecha_devolucion__gt=fecha_retiro,
                    estado__in=['PENDIENTE', 'CONFIRMADA']
                ).exists()
                
                if not reservas_existentes:
                    vehiculos_disponibles.append(vehiculo)
            
            context = {
                'sucursales': sucursales,
                'vehiculos_disponibles': vehiculos_disponibles,
                'fecha_retiro': fecha_retiro,
                'fecha_entrega': fecha_entrega,
                'sucursal_seleccionada': sucursal_retiro_id,
                'sucursal_devolucion_seleccionada': sucursal_devolucion_id,
                'misma_sucursal': misma_sucursal
            }
            return render(request, 'home/buscar_vehiculos.html', context)
        except (ValueError, TypeError):
            return render(request, 'home/buscar_vehiculos.html', {
                'sucursales': sucursales,
                'error': 'Error en el formato de los datos',
                'fecha_retiro': request.POST.get('fecha_retiro'),
                'fecha_entrega': request.POST.get('fecha_entrega'),
                'sucursal_seleccionada': request.POST.get('sucursal_retiro'),
                'misma_sucursal': request.POST.get('misma_sucursal') == 'on'
            })
    
    # Si es GET, mostrar el formulario con valores por defecto
    return render(request, 'home/buscar_vehiculos.html', {
        'sucursales': sucursales,
        'misma_sucursal': True
    })
