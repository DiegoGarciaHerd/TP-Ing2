from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import datetime

from .models import Reserva
from sucursales.models import Sucursal 
from vehiculos.models import Vehiculo
from .forms import ReservaForm, PagoForm
from .utils import procesar_pago_tarjeta




class VehiculoListView(ListView):
    model = Vehiculo
    template_name = 'sucursales/vehiculo_list.html' 
    context_object_name = 'vehiculos'

    def get_queryset(self):
        sucursal_id = self.kwargs.get('sucursal_id')
        if sucursal_id:
            return Vehiculo.objects.filter(sucursal_actual_id=sucursal_id, disponible=True)
        return Vehiculo.objects.filter(disponible=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sucursal_id = self.kwargs.get('sucursal_id')
        if sucursal_id:
            context['sucursal'] = get_object_or_404(Sucursal, pk=sucursal_id)
        return context


class VehiculoDetailView(DetailView):
    model = Vehiculo
    template_name = 'sucursales/vehiculo_detail.html' 
    context_object_name = 'vehiculo'



@login_required 
def crear_reserva(request, vehiculo_id):
    # --- AÑADIR ESTA VERIFICACIÓN AQUÍ ---
    if request.user.is_superuser: # O request.user.is_admin si tu modelo Usuario tiene ese campo
        messages.error(request, 'Los administradores no pueden realizar reservas de vehículos.')
        # Puedes redirigir a donde consideres más apropiado para un admin
        # Por ejemplo, al home del admin, o a la página principal del sitio.
        return redirect('admin_menu') # O a 'home:home' si prefieres que vayan al home principal
    # --- FIN DE LA VERIFICACIÓN ---

    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)

    if not vehiculo.disponible:
        messages.error(request, 'Este vehículo no está disponible para reserva en este momento.')
        return redirect('reservas:vehiculo_detail', pk=vehiculo.id) 

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            # Verificar disponibilidad sin guardar la reserva
            fecha_recogida = form.cleaned_data['fecha_recogida']
            fecha_devolucion = form.cleaned_data['fecha_devolucion']
            conductor_nombre = form.cleaned_data['conductor_nombre']
            conductor_apellido = form.cleaned_data['conductor_apellido']
            conductor_dni = form.cleaned_data['conductor_dni']

            reservas_existentes = Reserva.objects.filter(
                vehiculo=vehiculo,
                fecha_recogida__lt=fecha_devolucion, 
                fecha_devolucion__gt=fecha_recogida, 
                estado__in=['PENDIENTE', 'CONFIRMADA'] 
            )

            if reservas_existentes.exists():
                messages.error(request, 'El vehículo ya está reservado para el período seleccionado. Por favor, elige otras fechas.')
                return render(request, 'reservas/crear_reserva.html', {'form': form, 'vehiculo': vehiculo})

            # Calcular el costo total
            dias = (fecha_devolucion - fecha_recogida).days
            if dias > 0:
                costo_total = dias * vehiculo.precio_por_dia
            else:
                costo_total = vehiculo.precio_por_dia  # Cobrar por un día si las fechas son iguales
            
            # Guardar temporalmente en la sesión
            request.session['reserva_temporal'] = {
                'vehiculo_id': vehiculo.id,
                'fecha_recogida': fecha_recogida.isoformat(),
                'fecha_devolucion': fecha_devolucion.isoformat(),
                'costo_total': float(costo_total),
                'conductor_nombre': conductor_nombre,
                'conductor_apellido': conductor_apellido,
                'conductor_dni': conductor_dni
            }
            
            # Redirigir al ticket virtual
            return redirect('reservas:ticket_reserva', vehiculo_id=vehiculo.id)
    else:
        # Inicializar el formulario con las fechas de la URL si están presentes
        initial_data = {}
        fecha_retiro = request.GET.get('fecha_retiro')
        fecha_entrega = request.GET.get('fecha_entrega')
        
        if fecha_retiro:
            initial_data['fecha_recogida'] = fecha_retiro
        if fecha_entrega:
            initial_data['fecha_devolucion'] = fecha_entrega
            
        form = ReservaForm(initial=initial_data)
        
    return render(request, 'reservas/crear_reserva.html', {'form': form, 'vehiculo': vehiculo})



@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(cliente=request.user).order_by('-fecha_creacion')
    context = {
        'reservas': reservas,
        'today': datetime.date.today()
    }
    return render(request, 'reservas/mis_reservas.html', context)


@login_required
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, cliente=request.user)
    context = {
        'reserva': reserva,
        'today': datetime.date.today()
    }
    return render(request, 'reservas/detalle_reserva.html', context)


@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, cliente=request.user)

    if reserva.estado in ['PENDIENTE', 'CONFIRMADA'] and reserva.fecha_recogida >= datetime.date.today():
        if request.method == 'POST':
            reserva.estado = 'CANCELADA'
            reserva.save()
            return redirect('reservas:mis_reservas')
        context = {
            'reserva': reserva,
            'today': datetime.date.today()
        }
        return render(request, 'reservas/confirmar_cancelacion.html', context)
    else:
        messages.error(request, 'No se puede cancelar esta reserva.')
        return redirect('reservas:mis_reservas')

@login_required
def ticket_reserva(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    reserva_temporal = request.session.get('reserva_temporal')
    
    if not reserva_temporal or reserva_temporal['vehiculo_id'] != vehiculo.id:
        messages.error(request, 'No hay datos de reserva disponibles.')
        return redirect('home:home')
    
    # Crear un objeto Reserva temporal para mostrar en el template
    reserva = Reserva(
        cliente=request.user,
        vehiculo=vehiculo,
        fecha_recogida=datetime.datetime.fromisoformat(reserva_temporal['fecha_recogida']).date(),
        fecha_devolucion=datetime.datetime.fromisoformat(reserva_temporal['fecha_devolucion']).date(),
        costo_total=reserva_temporal['costo_total'],
        estado='PENDIENTE',
        conductor_nombre=reserva_temporal.get('conductor_nombre', ''),
        conductor_apellido=reserva_temporal.get('conductor_apellido', ''),
        conductor_dni=reserva_temporal.get('conductor_dni', '')
    )
    
    return render(request, 'reservas/ticket_reserva.html', {'reserva': reserva, 'vehiculo': vehiculo})

@login_required
def procesar_pago(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    
    # Verificar que exista una reserva temporal en la sesión
    if 'reserva_temporal' not in request.session:
        messages.error(request, 'No hay información de reserva. Por favor, crea una nueva reserva.')
        return redirect('reservas:crear_reserva', vehiculo_id=vehiculo.id)
    
    reserva_temporal = request.session['reserva_temporal']
    
    # Crear objeto de reserva temporal para mostrar
    reserva = type('Reserva', (), {
        'vehiculo': vehiculo,
        'fecha_recogida': datetime.datetime.strptime(reserva_temporal['fecha_recogida'], '%Y-%m-%d').date(),
        'fecha_devolucion': datetime.datetime.strptime(reserva_temporal['fecha_devolucion'], '%Y-%m-%d').date(),
        'costo_total': reserva_temporal['costo_total']
    })()
    
    if request.method == 'POST':
        form = PagoForm(request.POST, usuario=request.user)
        if form.is_valid():
            usar_tarjeta_guardada = form.cleaned_data.get('usar_tarjeta_guardada', False)
            
            if usar_tarjeta_guardada:
                # Usar tarjeta guardada
                try:
                    tarjeta_guardada = request.user.tarjeta_guardada
                    numero_tarjeta = tarjeta_guardada.obtener_numero_desencriptado()
                    nombre_titular = tarjeta_guardada.nombre_titular
                    mes_vencimiento = tarjeta_guardada.mes_vencimiento
                    ano_vencimiento = tarjeta_guardada.ano_vencimiento
                except:
                    messages.error(request, 'No se pudo acceder a tu tarjeta guardada. Por favor, ingresa los datos manualmente.')
                    return render(request, 'reservas/procesar_pago.html', {
                        'form': form, 
                        'reserva': reserva, 
                        'vehiculo': vehiculo
                    })
            else:
                # Usar datos del formulario
                numero_tarjeta = form.cleaned_data['numero_tarjeta']
                nombre_titular = form.cleaned_data['nombre_titular']
                mes_vencimiento = form.cleaned_data['mes_vencimiento']
                ano_vencimiento = form.cleaned_data['ano_vencimiento']
            
            # Procesar el pago
            resultado_pago = procesar_pago_tarjeta(
                numero_tarjeta=numero_tarjeta,
                nombre_titular=nombre_titular,
                mes_vencimiento=mes_vencimiento,
                ano_vencimiento=ano_vencimiento,
                cvv=form.cleaned_data['cvv'],
                monto=reserva_temporal['costo_total']
            )
            
            if resultado_pago['exito']:
                # Guardar tarjeta automáticamente si no usó una guardada
                if not usar_tarjeta_guardada:
                    try:
                        from usuarios.models import TarjetaGuardada
                        TarjetaGuardada.crear_tarjeta(
                            usuario=request.user,
                            numero_tarjeta=numero_tarjeta,
                            nombre_titular=nombre_titular,
                            mes_vencimiento=int(mes_vencimiento),
                            ano_vencimiento=int(ano_vencimiento)
                        )
                        messages.success(request, 'Pago exitoso. Tu tarjeta ha sido guardada automáticamente para futuras reservas.')
                    except Exception as e:
                        # No fallar el pago si hay error guardando la tarjeta
                        messages.warning(request, 'El pago fue exitoso, pero hubo un problema guardando la tarjeta.')
                else:
                    messages.success(request, '¡Pago procesado exitosamente con tu tarjeta guardada!')
                
                # Guardar información del pago en la sesión
                request.session['pago_procesado'] = {
                    'referencia_pago': resultado_pago['referencia_pago'],
                    'ultimos_4_digitos': resultado_pago['ultimos_4_digitos'],
                    'fecha_pago': resultado_pago['fecha_procesamiento'].isoformat(),
                    'monto': float(resultado_pago['monto_procesado'])
                }
                
                return redirect('reservas:confirmar_reserva', vehiculo_id=vehiculo.id)
            else:
                messages.error(request, f'Error en el pago: {resultado_pago["mensaje"]}')
                # Mantener los datos del formulario en caso de error
                return render(request, 'reservas/procesar_pago.html', {
                    'form': form, 
                    'reserva': reserva, 
                    'vehiculo': vehiculo,
                    'error_pago': resultado_pago
                })
    else:
        form = PagoForm(usuario=request.user)
    
    return render(request, 'reservas/procesar_pago.html', {
        'form': form, 
        'reserva': reserva, 
        'vehiculo': vehiculo
    })

@login_required
def confirmar_reserva(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    reserva_temporal = request.session.get('reserva_temporal')
    pago_procesado = request.session.get('pago_procesado')
    
    if not reserva_temporal or reserva_temporal['vehiculo_id'] != vehiculo.id:
        messages.error(request, 'No hay datos de reserva disponibles.')
        return redirect('home:home')
    
    if not pago_procesado:
        messages.error(request, 'Debe completar el pago antes de confirmar la reserva.')
        return redirect('reservas:procesar_pago', vehiculo_id=vehiculo.id)
    
    # Verificar disponibilidad una vez más antes de guardar
    fecha_recogida = datetime.datetime.fromisoformat(reserva_temporal['fecha_recogida']).date()
    fecha_devolucion = datetime.datetime.fromisoformat(reserva_temporal['fecha_devolucion']).date()
    conductor_nombre = reserva_temporal.get('conductor_nombre', '')
    conductor_apellido = reserva_temporal.get('conductor_apellido', '')
    conductor_dni = reserva_temporal.get('conductor_dni', '')
    
    reservas_existentes = Reserva.objects.filter(
        vehiculo=vehiculo,
        fecha_recogida__lt=fecha_devolucion, 
        fecha_devolucion__gt=fecha_recogida, 
        estado__in=['PENDIENTE', 'CONFIRMADA'] 
    )
    
    if reservas_existentes.exists():
        messages.error(request, 'El vehículo ya no está disponible para las fechas seleccionadas.')
        return redirect('home:home')
    
    # Crear y guardar la reserva con información de pago
    reserva = Reserva(
        cliente=request.user,
        vehiculo=vehiculo,
        fecha_recogida=fecha_recogida,
        fecha_devolucion=fecha_devolucion,
        costo_total=reserva_temporal['costo_total'],
        estado='CONFIRMADA',
        # Información de pago
        estado_pago='PAGADO',
        fecha_pago=datetime.datetime.fromisoformat(pago_procesado['fecha_pago']),
        referencia_pago=pago_procesado['referencia_pago'],
        ultimos_4_digitos_tarjeta=pago_procesado['ultimos_4_digitos'],
        # Datos del conductor
        conductor_nombre=conductor_nombre,
        conductor_apellido=conductor_apellido,
        conductor_dni=conductor_dni
    )
    reserva.save()
    
    # Enviar correo de confirmación
    try:
        # Obtener el email del usuario
        user_email = request.user.email
        if not user_email:
            raise ValueError("El usuario no tiene un email registrado")
            
        print(f"Intentando enviar correo a: {user_email}")
        print(f"Desde: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Usando servidor: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        
        context = {
            'reserva': reserva,
            'vehiculo': vehiculo
        }
        
        # Renderizar el template HTML
        email_html = render_to_string('reservas/email_reserva_confirmada.html', context)
        
        # Versión de texto plano
        email_text = f"""
        Confirmación de Reserva - AutoRental
        
        Hola {reserva.cliente.first_name},
        
        Tu reserva ha sido confirmada exitosamente. A continuación encontrarás los detalles de tu reserva:
        
        Reserva #{reserva.id}
        Estado: Confirmada
        
        Detalles del Vehículo:
        - Marca y Modelo: {reserva.vehiculo.marca} {reserva.vehiculo.modelo}
        - Patente: {reserva.vehiculo.patente}
        - Precio por día: ${reserva.vehiculo.precio_por_dia:.2f}
        
        Detalles de la Reserva:
        - Duración: {(reserva.fecha_devolucion - reserva.fecha_recogida).days} días
        - Estado: Pago Confirmado
        
        Retiro del Vehículo:
        - Sucursal: {reserva.vehiculo.sucursal_actual.nombre}
        - Dirección: {reserva.vehiculo.sucursal_actual.direccion}
        - Fecha: {reserva.fecha_recogida.strftime('%d/%m/%Y')}
        
        Devolución del Vehículo:
        - Sucursal: {reserva.vehiculo.sucursal_actual.nombre}
        - Dirección: {reserva.vehiculo.sucursal_actual.direccion}
        - Fecha: {reserva.fecha_devolucion.strftime('%d/%m/%Y')}
        
        Información de Pago:
        - Estado: Pagado
        - Referencia: {reserva.referencia_pago}
        - Tarjeta: ****{reserva.ultimos_4_digitos_tarjeta}
        - Fecha de Pago: {reserva.fecha_pago.strftime('%d/%m/%Y %H:%M')}
        
        Costo Total: ${reserva.costo_total:.2f}
        
        Este correo sirve como comprobante de tu reserva. Por favor, guárdalo para tus registros.
        Si tienes alguna pregunta, no dudes en contactarnos.
        
        Saludos,
        El equipo de AutoRental
        """
        
        # Crear y enviar el correo
        email = EmailMultiAlternatives(
            subject=f'Autorental - Reserva #{reserva.id}',
            body=email_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]  # Usar el email del usuario actual
        )
        email.attach_alternative(email_html, "text/html")
        email.send()
        print("Correo enviado exitosamente")
        
    except Exception as e:
        # No fallar la reserva si hay error en el envío del correo
        print(f"Error al enviar el correo de confirmación: {str(e)}")
        messages.warning(request, f'La reserva se ha confirmado, pero hubo un problema al enviar el correo de confirmación: {str(e)}')
    
    # Limpiar la sesión
    del request.session['reserva_temporal']
    del request.session['pago_procesado']
    
    # Mostrar página de confirmación exitosa directamente
    return render(request, 'reservas/reserva_confirmada.html', {
        'reserva': reserva,
        'vehiculo': vehiculo
    })

@login_required
def seleccionar_metodo_pago(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    
    # Verificar que exista una reserva temporal en la sesión
    if 'reserva_temporal' not in request.session:
        messages.error(request, 'No hay información de reserva. Por favor, crea una nueva reserva.')
        return redirect('reservas:crear_reserva', vehiculo_id=vehiculo.id)
    
    reserva_temporal = request.session['reserva_temporal']
    
    # Crear objeto de reserva temporal para mostrar
    reserva = type('Reserva', (), {
        'vehiculo': vehiculo,
        'fecha_recogida': datetime.datetime.strptime(reserva_temporal['fecha_recogida'], '%Y-%m-%d').date(),
        'fecha_devolucion': datetime.datetime.strptime(reserva_temporal['fecha_devolucion'], '%Y-%m-%d').date(),
        'costo_total': reserva_temporal['costo_total']
    })()
    
    if request.method == 'POST':
        # Simular pago exitoso con tarjeta guardada
        # Generar una referencia de pago única
        referencia_pago = f"PAY-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Guardar información del pago en la sesión
        request.session['pago_procesado'] = {
            'referencia_pago': referencia_pago,
            'ultimos_4_digitos': '****',  # En una implementación real, obtendríamos esto de la tarjeta guardada
            'fecha_pago': datetime.datetime.now().isoformat(),
            'monto': float(reserva_temporal['costo_total'])
        }
        
        messages.success(request, '¡Pago procesado exitosamente con tu tarjeta guardada!')
        return redirect('reservas:confirmar_reserva', vehiculo_id=vehiculo.id)
    
    # Verificar si el usuario tiene tarjeta guardada
    tarjeta_guardada = None
    try:
        tarjeta_guardada = request.user.tarjeta_guardada
    except:
        # Si no tiene tarjeta guardada, redirigir directamente a la página de pago
        return redirect('reservas:procesar_pago', vehiculo_id=vehiculo.id)
    
    return render(request, 'reservas/seleccionar_metodo_pago.html', {
        'reserva': reserva,
        'vehiculo': vehiculo,
        'tarjeta_guardada': tarjeta_guardada
    })
