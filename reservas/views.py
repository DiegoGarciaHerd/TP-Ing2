from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from decimal import Decimal
import datetime
import re

from .models import Reserva
from sucursales.models import Sucursal 
from vehiculos.models import Vehiculo
from .forms import ReservaForm, PagoForm, ExtrasReservaForm
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
    if request.user.is_superuser: 
        messages.error(request, 'Los administradores no pueden realizar reservas de vehículos.')
        return redirect('admin_menu') 

    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)

    if not vehiculo.disponible:
        messages.error(request, 'Este vehículo no está disponible para reserva en este momento.')
        return redirect('reservas:vehiculo_detail', pk=vehiculo.id) 

    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            fecha_recogida = form.cleaned_data['fecha_recogida']
            fecha_devolucion = form.cleaned_data['fecha_devolucion']
            conductor_nombre = form.cleaned_data['conductor_nombre']
            conductor_apellido = form.cleaned_data['conductor_apellido']
            conductor_dni = form.cleaned_data['conductor_dni']

            # Obtener los extras seleccionados
            silla_para_ninos = form.cleaned_data.get('silla_para_ninos', False)
            telepass = form.cleaned_data.get('telepass', False)
            seguro_por_danos = form.cleaned_data.get('seguro_por_danos', False)
            conductor_adicional = form.cleaned_data.get('conductor_adicional', False)
            conductor_adicional_nombre = form.cleaned_data.get('conductor_adicional_nombre', '')
            conductor_adicional_apellido = form.cleaned_data.get('conductor_adicional_apellido', '')
            conductor_adicional_dni = form.cleaned_data.get('conductor_adicional_dni', '')

            reservas_existentes = Reserva.objects.filter(
                vehiculo=vehiculo,
                fecha_recogida__lt=fecha_devolucion, 
                fecha_devolucion__gt=fecha_recogida, 
                estado__in=['PENDIENTE', 'CONFIRMADA'] 
            )

            if reservas_existentes.exists():
                messages.error(request, 'El vehículo ya está reservado para el período seleccionado. Por favor, elige otras fechas.')
                return render(request, 'reservas/crear_reserva.html', {'form': form, 'vehiculo': vehiculo})

            dias = (fecha_devolucion - fecha_recogida).days
            if dias > 0:
                costo_total = Decimal(str(vehiculo.precio_por_dia)) * Decimal(str(dias))
            else:
                costo_total = Decimal(str(vehiculo.precio_por_dia))
            
            # Calcular el costo total incluyendo extras
            extras_total = Decimal('0.00')
            if silla_para_ninos:
                extras_total += Decimal('1000.00') * Decimal(str(dias))
            if telepass:
                extras_total += Decimal('2000.00') * Decimal(str(dias))
            if seguro_por_danos:
                extras_total += costo_total * Decimal('0.30')
            if conductor_adicional:
                extras_total += costo_total * Decimal('0.20')
            
            precio_total = costo_total + extras_total
            
            request.session['reserva_temporal'] = {
                'vehiculo_id': vehiculo.id,
                'fecha_recogida': fecha_recogida.isoformat(),
                'fecha_devolucion': fecha_devolucion.isoformat(),
                'costo_total': float(costo_total),  # Convertir a float para la sesión
                'precio_total': float(precio_total),  # Convertir a float para la sesión
                'conductor_nombre': conductor_nombre,
                'conductor_apellido': conductor_apellido,
                'conductor_dni': conductor_dni,
                # Guardar los extras seleccionados
                'silla_para_ninos': silla_para_ninos,
                'telepass': telepass,
                'seguro_por_danos': seguro_por_danos,
                'conductor_adicional': conductor_adicional,
                'conductor_adicional_nombre': conductor_adicional_nombre,
                'conductor_adicional_apellido': conductor_adicional_apellido,
                'conductor_adicional_dni': conductor_adicional_dni
            }
            
            return redirect('reservas:ticket_reserva', vehiculo_id=vehiculo.id)
    else:
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
        monto_a_reembolsar_estimado = Decimal('0.00')

        if reserva.costo_total is not None and \
           hasattr(reserva.vehiculo, 'politica_de_reembolso') and \
           reserva.vehiculo.politica_de_reembolso is not None:
            try:
                politica_porcentaje = Decimal(str(reserva.vehiculo.politica_de_reembolso))
                monto_a_reembolsar_estimado = (reserva.costo_total * politica_porcentaje) / Decimal('100.00')
            except (TypeError, ValueError, AttributeError) as e:
                print(f"Error al calcular el monto de reembolso estimado: {e}")
                monto_a_reembolsar_estimado = Decimal('0.00')

        if request.method == 'POST':
            reserva.estado = 'CANCELADA'
            reserva.save() 

            if reserva.monto_a_reembolsar is not None and reserva.monto_a_reembolsar > 0:
                try:
                    from core.models import AdminBalance
                    admin_balance, created = AdminBalance.objects.get_or_create(pk=1)
                    admin_balance.saldo -= reserva.monto_a_reembolsar
                    admin_balance.save()
                    messages.success(request, f'La reserva ha sido cancelada exitosamente y se procesó un reembolso de ${reserva.monto_a_reembolsar:.2f}.')
                except Exception as e:
                    messages.error(request, f"La reserva fue cancelada, pero hubo un problema al ajustar el saldo del sistema para el reembolso: {e}")
            else:
                messages.info(request, 'La reserva ha sido cancelada. No aplica reembolso bajo la política actual.')

            return redirect('reservas:mis_reservas')
        else:
            context = {
                'reserva': reserva,
                'today': datetime.date.today(),
                'monto_a_reembolsar_estimado': monto_a_reembolsar_estimado,
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
        costo_total=Decimal(str(reserva_temporal['costo_total'])),  # Convertir a Decimal
        estado='PENDIENTE',
        conductor_nombre=reserva_temporal.get('conductor_nombre', ''),
        conductor_apellido=reserva_temporal.get('conductor_apellido', ''),
        conductor_dni=reserva_temporal.get('conductor_dni', ''),
        # Agregar los extras seleccionados
        silla_para_ninos=reserva_temporal.get('silla_para_ninos', False),
        telepass=reserva_temporal.get('telepass', False),
        seguro_por_danos=reserva_temporal.get('seguro_por_danos', False),
        conductor_adicional=reserva_temporal.get('conductor_adicional', False),
        conductor_adicional_nombre=reserva_temporal.get('conductor_adicional_nombre', ''),
        conductor_adicional_apellido=reserva_temporal.get('conductor_adicional_apellido', ''),
        conductor_adicional_dni=reserva_temporal.get('conductor_adicional_dni', '')
    )
    
    # Calcular el precio total incluyendo extras
    dias = (reserva.fecha_devolucion - reserva.fecha_recogida).days
    extras_total = Decimal('0.00')
    
    if reserva.silla_para_ninos:
        extras_total += Decimal('1000.00') * Decimal(str(dias))
    if reserva.telepass:
        extras_total += Decimal('2000.00') * Decimal(str(dias))
    if reserva.seguro_por_danos:
        extras_total += reserva.costo_total * Decimal('0.30')
    if reserva.conductor_adicional:
        extras_total += reserva.costo_total * Decimal('0.20')
    
    reserva.precio_total = reserva.costo_total + extras_total
    
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
                    
                    # Validar CVV específico para tarjeta guardada
                    cvv = form.cleaned_data['cvv']
                    numero_limpio = re.sub(r'[\s-]', '', numero_tarjeta)
                    
                    # Tarjetas permitidas con sus CVV específicos
                    tarjetas_permitidas = {
                        '4517660196851645': '789',
                        '5258556802017961': '345'
                    }
                    
                    if numero_limpio in tarjetas_permitidas:
                        if cvv != tarjetas_permitidas[numero_limpio]:
                            messages.error(request, 'CVV incorrecto para esta tarjeta.')
                            return render(request, 'reservas/procesar_pago.html', {
                                'form': form, 
                                'reserva': reserva, 
                                'vehiculo': vehiculo
                            })
                    else:
                        messages.error(request, 'Tarjeta no autorizada.')
                        return render(request, 'reservas/procesar_pago.html', {
                            'form': form, 
                            'reserva': reserva, 
                            'vehiculo': vehiculo
                        })
                        
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
    
    # Crear y guardar la reserva con información de pago y extras
    reserva = Reserva(
        cliente=request.user,
        vehiculo=vehiculo,
        fecha_recogida=fecha_recogida,
        fecha_devolucion=fecha_devolucion,
        costo_total=reserva_temporal['costo_total'],
        precio_total=reserva_temporal['precio_total'],
        estado='CONFIRMADA',
        # Información de pago
        estado_pago='PAGADO',
        fecha_pago=datetime.datetime.fromisoformat(pago_procesado['fecha_pago']),
        referencia_pago=pago_procesado['referencia_pago'],
        ultimos_4_digitos_tarjeta=pago_procesado['ultimos_4_digitos'],
        # Datos del conductor
        conductor_nombre=conductor_nombre,
        conductor_apellido=conductor_apellido,
        conductor_dni=conductor_dni,
        # Extras seleccionados
        silla_para_ninos=reserva_temporal.get('silla_para_ninos', False),
        telepass=reserva_temporal.get('telepass', False),
        seguro_por_danos=reserva_temporal.get('seguro_por_danos', False),
        conductor_adicional=reserva_temporal.get('conductor_adicional', False),
        conductor_adicional_nombre=reserva_temporal.get('conductor_adicional_nombre', ''),
        conductor_adicional_apellido=reserva_temporal.get('conductor_adicional_apellido', ''),
        conductor_adicional_dni=reserva_temporal.get('conductor_adicional_dni', '')
    )
    reserva.save()

    try:
        from core.models import AdminBalance
        admin_balance, created = AdminBalance.objects.get_or_create(pk=1)
        admin_balance.saldo += Decimal(str(reserva.precio_total))  # Usar precio_total en lugar de costo_total
        admin_balance.save()
    except Exception as e:
        messages.warning(request, f"Reserva confirmada, pero hubo un problema actualizando el saldo del sistema: {e}")
    
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
        
        Costo Total: ${reserva.precio_total:.2f}
        
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
    if 'reserva_temporal' in request.session:
        del request.session['reserva_temporal']
    if 'pago_procesado' in request.session:
        del request.session['pago_procesado']

    messages.success(request, '¡Reserva confirmada exitosamente!')
    return redirect('reservas:detalle_reserva', reserva_id=reserva.id)

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
        try:
            tarjeta_guardada = request.user.tarjeta_guardada
            cvv = request.POST.get('cvv')
            
            # Tarjetas permitidas con sus CVV específicos
            tarjetas_permitidas = {
                '4517660196851645': '789',
                '5258556802017961': '345'
            }
            
            ultimos_4_digitos = tarjeta_guardada.ultimos_4_digitos
            
            if ultimos_4_digitos in tarjetas_permitidas:
                if cvv != tarjetas_permitidas[ultimos_4_digitos]:
                    messages.error(request, 'CVV incorrecto para esta tarjeta.')
                    return render(request, 'reservas/seleccionar_metodo_pago.html', {
                        'reserva': reserva,
                        'vehiculo': vehiculo,
                        'tarjeta_guardada': tarjeta_guardada
                    })
            else:
                messages.error(request, 'Tarjeta no autorizada.')
                return render(request, 'reservas/seleccionar_metodo_pago.html', {
                    'reserva': reserva,
                    'vehiculo': vehiculo,
                    'tarjeta_guardada': tarjeta_guardada
                })
            
            # Si el CVV es correcto, proceder con el pago
            referencia_pago = f"PAY-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Guardar información del pago en la sesión
            request.session['pago_procesado'] = {
                'referencia_pago': referencia_pago,
                'ultimos_4_digitos': tarjeta_guardada.ultimos_4_digitos,
                'fecha_pago': datetime.datetime.now().isoformat(),
                'monto': float(reserva_temporal['costo_total'])
            }
            
            return redirect('reservas:confirmar_reserva', vehiculo_id=vehiculo.id)
            
        except Exception as e:
            messages.error(request, 'Error al procesar el pago. Por favor, intenta nuevamente.')
            return render(request, 'reservas/seleccionar_metodo_pago.html', {
                'reserva': reserva,
                'vehiculo': vehiculo,
                'tarjeta_guardada': request.user.tarjeta_guardada
            })
    
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

@login_required
def actualizar_extras(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, cliente=request.user)
    
    if reserva.estado != 'PENDIENTE':
        messages.error(request, "Solo se pueden modificar los extras de reservas pendientes.")
        return redirect('reservas:detalle_reserva', reserva_id=reserva.id)
    
    if request.method == 'POST':
        form = ExtrasReservaForm(request.POST, instance=reserva)
        if form.is_valid():
            form.save()
            messages.success(request, "Los extras han sido actualizados correctamente.")
            return redirect('reservas:detalle_reserva', reserva_id=reserva.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = ExtrasReservaForm(instance=reserva)
    
    return redirect('reservas:detalle_reserva', reserva_id=reserva.id)