
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from vehiculos.models import Vehiculo
from .decorators import empleado_required 
from reservas.models import Reserva # ¡Asegúrate de importar el modelo Reserva!
from django.utils import timezone # ¡Asegúrate de importar timezone!
from django.db import transaction
from django.http import JsonResponse
from decimal import Decimal 

@empleado_required # Aplica el decorador aquí
def menu_empleado(request):
    return render(request, 'empleados/menu_empleado.html')

# Las otras vistas de empleado también deberían ser protegidas
@empleado_required
def buscar_cliente(request):
    return render(request, 'empleados/buscar_cliente.html')

@empleado_required
def modificar_vehiculo(request):
    vehiculos = Vehiculo.objects.all().order_by('patente')

    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
           vehiculo = Vehiculo.objects.get(patente=patente)
           
           if kilometraje := request.POST.get('kilometraje'):
               vehiculo.kilometraje = int(kilometraje)
           if disponibilidad := request.POST.get('disponibilidad'):
               vehiculo.disponible = disponibilidad

        except Vehiculo.DoesNotExist:
            messages.error(request, "El vehículo no existe.")
        except ValueError:
            messages.error(request, "Kilometraje debe ser un número válido.")
        except Exception as e:
            messages.error(request, "Ocurrió un error al modificar el vehículo: " + str(e))     

    return render(request, 'empleados/modificar_vehiculo.html', {'vehiculos': vehiculos})

@empleado_required
def reserva_empleado(request):
    return render(request, 'empleados/reserva_empleado.html')


def login_empleado(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        usuario = authenticate(request, username=username, password=password)
        if usuario is not None:
            if hasattr(usuario, 'is_staff') and usuario.is_staff: 
                login(request, usuario)
                messages.success(request, "Inicio de sesión exitoso.")
                return redirect('empleados:menu_empleado')
            else:
                messages.error(request, "Tus credenciales no tienen permisos de empleado.")
                return redirect('empleados:login_empleado') 
        else:
            messages.error(request, "Credenciales inválidas. Por favor, inténtalo de nuevo.")

    return render(request, 'empleados/login_empleado.html')


@empleado_required
def modificar_autos(request):
    # Obtener todos los vehículos para el selector
    vehiculos = Vehiculo.objects.all().order_by('patente')
    
    if request.method == 'POST':
        patente = request.POST.get('patente')
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            
            # Actualizar campos si se proporcionaron
            # Estos campos ya estaban siendo actualizados
            if precio := request.POST.get('precio'):
                # Es crucial convertir a Decimal para el campo DecimalField
                vehiculo.precio_por_dia = Decimal(precio) 
            if foto := request.POST.get('foto_base64'):
                vehiculo.foto_base64 = foto
            if (politica_reembolso := request.POST.get('politica_reembolso')):
                vehiculo.politica_de_reembolso = politica_reembolso
            
            # --- ¡Añade estas líneas para guardar kilometraje y disponibilidad! ---
            if kilometraje_str := request.POST.get('kilometraje'):
                try:
                    vehiculo.kilometraje = int(kilometraje_str)
                except ValueError:
                    messages.error(request, "El kilometraje debe ser un número válido.")
                    # Si hay un error, no guardamos y volvemos a renderizar
                    return render(request, 'empleados/modificar_autos.html', {'vehiculos': vehiculos})

            disponibilidad_str = request.POST.get('disponible') # El nombre en HTML es 'disponible'
            if disponibilidad_str is not None: # Verifica si se envió el campo
                if disponibilidad_str == 'True':
                    vehiculo.disponible = True
                elif disponibilidad_str == 'False':
                    vehiculo.disponible = False
                # No necesitamos un 'else' si el HTML garantiza que solo serán 'True' o 'False'
            # --- Fin de las adiciones ---
            
            vehiculo.save() # Guarda todos los cambios en la base de datos
            messages.success(request, "Auto modificado exitosamente.")
            return redirect('empleados:menu_empleado') # Redirige al menú del empleado
            
        except Vehiculo.DoesNotExist:
            messages.error(request, "El auto a modificar no existe.")
        except Exception as e:
            # Captura cualquier otro error inesperado y lo muestra
            messages.error(request, f"Error al modificar el auto: {e}")
            
    # Si es un GET request o si hubo un error y se debe volver a renderizar el formulario
    return render(request, 'empleados/modificar_autos.html', {'vehiculos': vehiculos})


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
                #vehiculo.disponible = False # Marcar como no disponible al ser retirado
                vehiculo.save()

            messages.success(request, f"Retiro del auto {vehiculo.patente} para la reserva {reserva.id} confirmado exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al confirmar el retiro para la reserva {reserva.id}: {e}")
        
    return render(request, 'empleados/listar_retiros_pendientes.html') 


@empleado_required # ¡Protege también este endpoint!
def obtener_datos_vehiculo_ajax(request):
    patente = request.GET.get('patente')
    if not patente:
        return JsonResponse({'error': 'Patente no proporcionada'}, status=400) # Bad Request

    try:
        vehiculo = Vehiculo.objects.get(patente=patente)
        
        # Prepara los datos para enviar de vuelta
        data = {
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'kilometraje': vehiculo.kilometraje,
            'precio_por_dia': str(vehiculo.precio_por_dia), # Convierte Decimal a string
            'disponible': vehiculo.disponible,
            'politica_de_reembolso': str(vehiculo.politica_de_reembolso), # Convierte Decimal a string
            'foto_base64': vehiculo.foto_base64 # Asumiendo que esto es una cadena base64 o se puede enviar directamente
        }
        return JsonResponse(data)
    except Vehiculo.DoesNotExist:
        return JsonResponse({'error': 'Vehículo no encontrado'}, status=404) # Not Found
    except Exception as e:
        # Registra el error para depuración en el servidor
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error al obtener datos del vehículo {patente}: {e}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500) # Internal Server Error
