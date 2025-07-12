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
from usuarios.forms import EmpleadoRegistroClienteForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from .forms import EmpleadoEditarPerfilForm, EmpleadoCambiarPasswordForm
from .models import Empleado
from reservas.forms import ReservaForm
import datetime
import logging

logger = logging.getLogger(__name__)

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


@empleado_required 
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
        return JsonResponse({'error': 'Patente no proporcionada'}, status=400) # Bad Request

    try:
        vehiculo = Vehiculo.objects.get(patente=patente)
        
        # Verificar que el vehículo no esté dado de baja
        if vehiculo.estado == 'BAJA':
            return JsonResponse({'error': 'No se puede modificar un vehículo dado de baja'}, status=403) # Forbidden
        
        # Prepara los datos para enviar de vuelta
        data = {
            'marca': vehiculo.marca,
            'modelo': vehiculo.modelo,
            'kilometraje': vehiculo.kilometraje,
            'estado': vehiculo.estado,
            # --- ¡Estas líneas son las que debes eliminar o comentar! ---
            # 'precio_por_dia': str(vehiculo.precio_por_dia),
            # 'politica_de_reembolso': vehiculo.politica_de_reembolso,
            # 'foto_base64': vehiculo.foto_base64 or ''
            # -----------------------------------------------------------
        }
        return JsonResponse(data)
    except Vehiculo.DoesNotExist:
        return JsonResponse({'error': 'Vehículo no encontrado'}, status=404) # Not Found
    except Exception as e:
        logger.error(f"Error al obtener datos del vehículo {patente}: {e}")
        return JsonResponse({'error': 'Error interno del servidor'}, status=500) # Internal Server Error

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

            #Agregar penalizacion si la fecha de devolucion es mayor a la actual
            if reserva.fecha_devolucion < timezone.localdate():
                vehiculo_reserva = Vehiculo.objects.get(id=reserva.vehiculo.id)
                dias_retraso = (timezone.localdate() - reserva.fecha_devolucion).days
                penalizacion = Decimal(vehiculo_reserva.precio_por_dia) * Decimal(dias_retraso)
                messages.warning(request, f"Devolución del vehículo {vehiculo.marca} {vehiculo.modelo} ({vehiculo.patente}) para la reserva {reserva.id}"
                                 f" confirmada con {dias_retraso} días de retraso. Se aplicará una penalización de {penalizacion} al cliente."
                                 f" Kilometraje actualizado a {nuevo_kilometraje} km.")
            else:
                messages.success(request, f"Devolución del vehículo {vehiculo.marca} {vehiculo.modelo} ({vehiculo.patente}) para la reserva {reserva.id}"
                                 f"confirmada exitosamente. Kilometraje actualizado a {nuevo_kilometraje} km.")
            return redirect('empleados:listar_devoluciones_pendientes')

        except Exception as e:
            messages.error(request, f"Error al confirmar la devolución de la reserva {reserva.id}: {e}")
            return redirect('empleados:listar_devoluciones_pendientes')
    
    messages.error(request, "Método no permitido para esta acción.")
    return redirect('empleados:listar_devoluciones_pendientes')



@empleado_required # <--- ¡Aplica el decorador aquí!
def registrar_cliente(request):
    if request.method == 'POST':
        form = EmpleadoRegistroClienteForm(request.POST)
        if form.is_valid():
            try:
                nuevo_cliente, password_generada = form.save()
                enviar_cliente_credentials_email(request, nuevo_cliente.email, password_generada, nuevo_cliente.get_full_name())
                messages.success(request, f"¡Cliente {nuevo_cliente.email} registrado exitosamente! Se han enviado las credenciales por email.")
                # Limpiar el formulario después del registro exitoso
                form = EmpleadoRegistroClienteForm()
            except Exception as e:
                messages.error(request, f"Error al registrar cliente: {e}")
        else:
            messages.error(request, "Error en el formulario. Por favor, corrija los errores.")
    else:
        form = EmpleadoRegistroClienteForm()
    
    context = {
        'form': form
    }
    return render(request, 'empleados/registrar_cliente.html', context)

def enviar_cliente_credentials_email(request, user_email, password, client_name):
    """Envía email con las credenciales al cliente recién registrado"""
    context = {
        'client_name': client_name,
        'email': user_email,
        'password': password,
    }
    email_html = render_to_string('empleados/email_cliente_credenciales.html', context)
    email_text = f"Hola {client_name},\n\n" \
                 f"Tu cuenta en AutoRental ha sido creada exitosamente.\n" \
                 f"Tus credenciales para acceder al sistema son:\n" \
                 f"Email: {user_email}\n" \
                 f"Contraseña: {password}\n\n" \
                 f"Por razones de seguridad, te recomendamos cambiar tu contraseña al iniciar sesión por primera vez."

    email = EmailMultiAlternatives(
        subject='Bienvenido a AutoRental - Tus Credenciales de Acceso',
        body=email_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    email.attach_alternative(email_html, "text/html")
    try:
        email.send()
        messages.info(request, f"Credenciales enviadas a {user_email}")
    except Exception as e:
        messages.error(request, f"Error al enviar email a {user_email}: {e}")

@empleado_required
def editar_perfil_empleado(request):
    """Vista para que los empleados editen su perfil"""
    try:
        empleado = Empleado.objects.get(user=request.user)
    except Empleado.DoesNotExist:
        messages.error(request, "No se encontró tu perfil de empleado.")
        return redirect('empleados:menu_empleado')
    
    if request.method == 'POST':
        if 'cambiar_password' in request.POST:
            # Procesar cambio de contraseña
            form_password = EmpleadoCambiarPasswordForm(request.user, request.POST)
            if form_password.is_valid():
                form_password.save()
                messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
                return redirect('empleados:editar_perfil_empleado')
            # Si el formulario no es válido, también necesitamos form_perfil
            form_perfil = EmpleadoEditarPerfilForm(instance=empleado)
        else:
            # Procesar edición de perfil
            form_perfil = EmpleadoEditarPerfilForm(request.POST, instance=empleado)
            if form_perfil.is_valid():
                form_perfil.save()
                messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
                return redirect('empleados:editar_perfil_empleado')
            # Si el formulario no es válido, también necesitamos form_password
            form_password = EmpleadoCambiarPasswordForm(request.user)
    else:
        form_perfil = EmpleadoEditarPerfilForm(instance=empleado)
        form_password = EmpleadoCambiarPasswordForm(request.user)

    return render(request, 'empleados/editar_perfil_empleado.html', {
        'form_perfil': form_perfil,
        'form_password': form_password,
        'empleado': empleado
    })


@empleado_required
def empleados_seleccionar_vehiculo(request):
    """
    Permite al empleado seleccionar un vehículo para iniciar una nueva reserva.
    """
    # Puedes filtrar por disponibilidad, categoría, etc.
    vehiculos_disponibles = Vehiculo.objects.filter(estado='DISPONIBLE').order_by('marca', 'modelo')
    
    context = {
        'vehiculos': vehiculos_disponibles
    }
    return render(request, 'empleados/seleccionar_vehiculo.html', context) # Create this new template


@empleado_required
def empleados_crear_reserva(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)

    if vehiculo.estado != 'DISPONIBLE':
        messages.error(request, 'Este vehículo no está disponible para reserva en este momento.')
        return redirect('sucursales:vehiculo_detail', pk=vehiculo.id)

    if request.method == 'POST':
        form = ReservaForm(request.POST, vehiculo=vehiculo, is_employee_context=True)
        if form.is_valid():
            cliente_seleccionado = form.cleaned_data['cliente_seleccionado']
            
            fecha_recogida = form.cleaned_data['fecha_recogida']
            fecha_devolucion = form.cleaned_data['fecha_devolucion']
            conductor_nombre = form.cleaned_data['conductor_nombre']
            conductor_apellido = form.cleaned_data['conductor_apellido']
            conductor_dni = form.cleaned_data['conductor_dni']
            
            # Verificar disponibilidad del vehículo (¡muy importante!)
            # Excluir la reserva actual SOLO si estuvieras editando una (no es el caso aquí)
            reservas_existentes = Reserva.objects.filter(
                vehiculo=vehiculo,
                fecha_recogida__lt=fecha_devolucion,
                fecha_devolucion__gt=fecha_recogida,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'RETIRADO']
            )
            # No es necesario el exclude(pk=form.instance.pk) porque estamos creando una nueva

            if reservas_existentes.exists():
                messages.error(request, 'El vehículo ya está reservado para el período seleccionado. Por favor, elige otras fechas.')
                return render(request, 'empleados/crear_reserva_para_cliente.html', {'form': form, 'vehiculo': vehiculo})

            # Calcula costos (como ya lo tenías)
            dias = (fecha_devolucion - fecha_recogida).days
            if dias <= 0:
                dias = 1
            costo_base = Decimal(str(vehiculo.precio_por_dia)) * Decimal(str(dias))
            
            extras_total = Decimal('0.00')
            if form.cleaned_data.get('silla_para_ninos'): extras_total += Decimal('1000.00') * Decimal(str(dias))
            if form.cleaned_data.get('telepass'): extras_total += Decimal('2000.00') * Decimal(str(dias))
            if form.cleaned_data.get('seguro_por_danos'): extras_total += costo_base * Decimal('0.30')
            if form.cleaned_data.get('conductor_adicional'): extras_total += costo_base * Decimal('0.20')
            
            costo_total = costo_base + extras_total

            # --- CAMBIOS CLAVE AQUÍ ---
            # Guardamos la reserva temporal en la sesión (como un cliente)
            request.session['reserva_temporal'] = {
                'vehiculo_id': vehiculo.id,
                'fecha_recogida': fecha_recogida.isoformat(),
                'fecha_devolucion': fecha_devolucion.isoformat(),
                'costo_base': float(costo_base),
                'monto_adicional': float(extras_total),
                'costo_total': float(costo_total),
                'conductor_nombre': conductor_nombre,
                'conductor_apellido': conductor_apellido,
                'conductor_dni': conductor_dni,
                'silla_para_ninos': form.cleaned_data.get('silla_para_ninos', False),
                'telepass': form.cleaned_data.get('telepass', False),
                'seguro_por_danos': form.cleaned_data.get('seguro_por_danos', False),
                'conductor_adicional': form.cleaned_data.get('conductor_adicional', False),
                'conductor_adicional_nombre': form.cleaned_data.get('conductor_adicional_nombre', ''),
                'conductor_adicional_apellido': form.cleaned_data.get('conductor_adicional_apellido', ''),
                'conductor_adicional_dni': form.cleaned_data.get('conductor_adicional_dni', ''),
                
                'cliente_id': cliente_seleccionado.id, # ¡NUEVO! Guardamos el ID del cliente seleccionado
            }
            
            messages.info(request, 'Reserva iniciada. Por favor, procede con el pago.')
            # Redirigimos a la vista de pago
            return redirect('reservas:procesar_pago', vehiculo_id=vehiculo.id)

        else:
            # Si el formulario no es válido, mostrar los errores
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{form.fields[field].label}: {error}")
    else:
        form = ReservaForm(vehiculo=vehiculo, is_employee_context=True)

    context = {
        'form': form,
        'vehiculo': vehiculo,
    }
    return render(request, 'empleados/crear_reserva_para_cliente.html', context)

