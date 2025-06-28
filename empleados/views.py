from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from vehiculos.models import Vehiculo
from .decorators import empleado_required 
from reservas.models import Reserva 
from django.utils import timezone 
from django.db import transaction
from django.http import JsonResponse
from decimal import Decimal 
from usuarios.models import Usuario
from vehiculos.forms import VehiculoEmpleadoForm


@empleado_required 
def menu_empleado(request):
    return render(request, 'empleados/menu_empleado.html')


@empleado_required
def buscar_cliente(request):
    cliente = None
    reservas = None
    error_message = None
    
    if request.method == 'POST':
        dni_o_email = request.POST.get('dni_o_email', '').strip()
        
        if not dni_o_email:
            messages.error(request, "Por favor, ingrese un DNI o Email válido.")
        else:
            try:
                # Buscar por DNI si es numérico, sino por email
                if dni_o_email.isdigit():
                    cliente = Usuario.objects.get(DNI=dni_o_email, rol='CLIENTE')
                else:
                    cliente = Usuario.objects.get(email__iexact=dni_o_email, rol='CLIENTE')
                
                reservas = Reserva.objects.filter(cliente=cliente).order_by('-fecha_creacion')
                reservas_pendientes = reservas.filter(estado__in=['PENDIENTE', 'CONFIRMADA'])
                reservas_en_curso = reservas.filter(estado='RETIRADO')
                reservas_finalizadas = reservas.filter(estado='FINALIZADA')
                reservas_canceladas = reservas.filter(estado='CANCELADA')
                
                context = {
                    'cliente': cliente,
                    'reservas': reservas,
                    'reservas_pendientes': reservas_pendientes,
                    'reservas_en_curso': reservas_en_curso,
                    'reservas_finalizadas': reservas_finalizadas,
                    'reservas_canceladas': reservas_canceladas,
                    'total_reservas': reservas.count(),
                    'dni_o_email_buscado': dni_o_email,
                }
                
                messages.success(request, f"Cliente encontrado: {cliente.get_full_name()}")
                return render(request, 'empleados/buscar_cliente.html', context)
                
            except Usuario.DoesNotExist:
                messages.error(request, f"No se encontró ningún cliente con el dato ingresado: {dni_o_email}")
            except Exception as e:
                messages.error(request, f"Error al buscar el cliente: {str(e)}")
    
    return render(request, 'empleados/buscar_cliente.html', {
        'cliente': cliente,
        'reservas': reservas,
        'error_message': error_message
    })

@empleado_required
def reserva_empleado(request):
    return render(request, 'empleados/reserva_empleado.html')


@empleado_required
def modificar_autos(request):
    # Obtener todos los vehículos (excluyendo los dados de baja)
    vehiculos = Vehiculo.objects.exclude(estado='BAJA').order_by('patente')
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        if not patente:
            messages.error(request, "Debes seleccionar un vehículo")
            return render(request, 'empleados/modificar_autos.html', {'vehiculos': vehiculos})
        
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            
            # Actualizar campos
            if 'kilometraje' in request.POST:
                vehiculo.kilometraje = int(request.POST['kilometraje'])
            
            if 'estado' in request.POST:
                vehiculo.estado = request.POST['estado']
            
            if 'precio' in request.POST:
                vehiculo.precio_por_dia = Decimal(request.POST['precio'])
            
            if 'politica_reembolso' in request.POST:
                vehiculo.politica_de_reembolso = request.POST['politica_reembolso']
            
            # Manejo de imagen
            if 'foto' in request.FILES:
                # Procesar imagen y convertir a base64 si es necesario
                imagen = request.FILES['foto']
                vehiculo.foto_base64 = imagen.read().decode('latin1')  # Ajusta según tu implementación
            
            vehiculo.save()
            messages.success(request, "Vehículo modificado exitosamente")
            return redirect('empleados:modificar_autos')
            
        except Vehiculo.DoesNotExist:
            messages.error(request, "El vehículo seleccionado no existe")
        except ValueError as e:
            messages.error(request, f"Datos inválidos: {str(e)}")
        except Exception as e:
            messages.error(request, f"Error al modificar el vehículo: {str(e)}")
    
    # Renderizar el formulario (para GET o si hay errores)
    return render(request, 'empleados/modificar_autos.html', {
        'vehiculos': vehiculos,
        'form': request.POST if request.method == 'POST' else None
    })


@empleado_required # Aplicamos tu decorador de empleado
def listar_retiros_pendientes(request):
    hoy = timezone.localdate()

    retiros_pendientes = Reserva.objects.filter(
        fecha_recogida=hoy,
        estado__in=['PENDIENTE', 'CONFIRMADA'], # Filtra solo las que están pendientes de ser retiradas
        estado_pago='PAGADO' # Solo si el pago ya fue procesado para el retiro
    ).order_by('fecha_recogida', 'fecha_creacion')

    context = {
        'retiros_pendientes': retiros_pendientes,
        'hoy': hoy,
    }
    return render(request, 'empleados/listar_retiros_pendientes.html', context) 


@empleado_required
def confirmar_retiro_auto(request, reserva_id):
    if request.method == 'POST':
        reserva = get_object_or_404(Reserva, id=reserva_id)

        # Verificaciones adicionales:
        # 1. Asegúrate de que la fecha de recogida es hoy o una fecha pasada reciente para tolerar retiros tardíos
        if reserva.fecha_recogida > timezone.localdate():
            messages.error(request, f"El retiro de esta reserva (ID: {reserva.id}) no corresponde a la fecha actual.")
            return redirect('empleados:listar_retiros_pendientes') # <-- CAMBIO DE REDIRECCIÓN AQUÍ
        
        # 2. Asegúrate de que el estado actual permita el retiro (PENDIENTE o CONFIRMADA)
        if reserva.estado not in ['PENDIENTE', 'CONFIRMADA']:
            messages.warning(request, f"La reserva ID {reserva.id} ya ha sido retirada o su estado ({reserva.estado}) no permite el retiro.")
            return redirect('empleados:listar_retiros_pendientes') # <-- CAMBIO DE REDIRECCIÓN AQUÍ

        # 3. Asegúrate de que el estado de pago sea 'PAGADO' antes de permitir el retiro
        if reserva.estado_pago != 'PAGADO':
            messages.warning(request, f"La reserva ID {reserva.id} no está marcada como PAGADA. No se puede confirmar el retiro.")
            return redirect('empleados:listar_retiros_pendientes') # <-- CAMBIO DE REDIRECCIÓN AQUÍ

        try:
            with transaction.atomic():
                reserva.estado = 'RETIRADO'
                reserva.save()

                vehiculo = reserva.vehiculo
                vehiculo.save()

            messages.success(request, f"Retiro del auto {vehiculo.patente} para la reserva {reserva.id} confirmado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al confirmar el retiro para la reserva {reserva.id}: {e}")
        
    return render(request, 'empleados/listar_retiros_pendientes.html') 


@empleado_required
def obtener_datos_vehiculo_ajax(request):
    patente = request.GET.get('patente')
    if not patente:
        return JsonResponse({'error': 'Patente no proporcionada'}, status=400)  # Bad Request

    try:
        vehiculo = Vehiculo.objects.get(patente=patente)
        
        # Verificar que el vehículo no esté dado de baja
        if vehiculo.estado == 'BAJA':
            return JsonResponse({'error': 'No se puede modificar un vehículo dado de baja'}, status=403)  # Forbidden
        
        # Prepara los datos para enviar de vuelta
        data = {
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'kilometraje': vehiculo.kilometraje,
            'precio_por_dia': str(vehiculo.precio_por_dia),  # Convierte Decimal a string
            'estado': vehiculo.estado,  # Cambiamos 'disponible' por 'estado'
            'politica_de_reembolso': vehiculo.politica_de_reembolso,  # Ya es string en el modelo
            'foto_base64': vehiculo.foto_base64 or ''  # Asegura que no sea None
        }
        return JsonResponse(data)
    except Vehiculo.DoesNotExist:
        return JsonResponse({'error': 'Vehículo no encontrado'}, status=404)  # Not Found
    except Exception as e:
        # Registra el error para depuración en el servidor
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al obtener datos del vehículo {patente}: {e}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500)  # Internal Server Error


@empleado_required
def listar_devoluciones_pendientes(request):
    hoy = timezone.localdate()
    

    devoluciones_pendientes = Reserva.objects.filter(
        estado='RETIRADO', 
        #fecha_devolucion__lte=hoy
    ).order_by('fecha_devolucion', 'fecha_recogida') # Ordenar para mejor visualización

    context = {
        'devoluciones_pendientes': devoluciones_pendientes,
        'hoy': hoy,
    }
    return render(request, 'empleados/listar_devoluciones_pendientes.html', context)

@empleado_required
def confirmar_devolucion_auto(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)

    if request.method == 'POST':
        # Validación de estado: Asegurarse de que solo se pueda confirmar una reserva que fue retirada
        if reserva.estado != 'RETIRADO':
            messages.error(request, f"La reserva {reserva.id} no puede ser confirmada como devuelta. Su estado actual es '{reserva.estado}'.")
            return redirect('empleados:listar_devoluciones_pendientes')
        
        # Obtener y validar el kilometraje
        kilometraje_str = request.POST.get('kilometraje')
        if not kilometraje_str:
            messages.error(request, "Por favor, ingrese el kilometraje actual del vehículo.")
            return redirect('empleados:listar_devoluciones_pendientes') # Puedes redirigir a una página de detalle de reserva si existe

        try:
            nuevo_kilometraje = int(kilometraje_str)
            if nuevo_kilometraje < reserva.vehiculo.kilometraje:
                messages.error(request, f"El kilometraje ingresado ({nuevo_kilometraje} km) no puede ser menor que el kilometraje actual del vehículo ({reserva.vehiculo.kilometraje} km).")
                return redirect('empleados:listar_devoluciones_pendientes')
        except ValueError:
            messages.error(request, "El kilometraje debe ser un número válido.")
            return redirect('empleados:listar_devoluciones_pendientes')
            
        try:
            with transaction.atomic():
                reserva.estado = 'FINALIZADA' 
                reserva.save()
                vehiculo = reserva.vehiculo
                vehiculo.kilometraje = nuevo_kilometraje 
                vehiculo.estado = 'DISPONIBLE' 
                vehiculo.save()

            messages.success(request, f"Devolución del vehículo {vehiculo.marca} {vehiculo.modelo} ({vehiculo.patente}) para la reserva {reserva.id} confirmada exitosamente. Kilometraje actualizado a {nuevo_kilometraje} km.")
            return redirect('empleados:listar_devoluciones_pendientes')

        except Exception as e:
            messages.error(request, f"Error al confirmar la devolución de la reserva {reserva.id}: {e}")
            return redirect('empleados:listar_devoluciones_pendientes')
    
    messages.error(request, "Método no permitido para esta acción.")
    return redirect('empleados:listar_devoluciones_pendientes')