from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
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
            
            # Crear la reserva pero no guardarla aún
            reserva = Reserva(
                cliente=request.user,
                vehiculo=vehiculo,
                fecha_recogida=fecha_recogida,
                fecha_devolucion=fecha_devolucion,
                costo_total=costo_total,
                estado='PENDIENTE'
            )
            
            # Guardar temporalmente en la sesión
            request.session['reserva_temporal'] = {
                'vehiculo_id': vehiculo.id,
                'fecha_recogida': fecha_recogida.isoformat(),
                'fecha_devolucion': fecha_devolucion.isoformat(),
                'costo_total': float(costo_total)
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
        estado='PENDIENTE'
    )
    
    return render(request, 'reservas/ticket_reserva.html', {'reserva': reserva, 'vehiculo': vehiculo})

@login_required
def procesar_pago(request, vehiculo_id):
    vehiculo = get_object_or_404(Vehiculo, pk=vehiculo_id)
    reserva_temporal = request.session.get('reserva_temporal')
    
    if not reserva_temporal or reserva_temporal['vehiculo_id'] != vehiculo.id:
        messages.error(request, 'No hay datos de reserva disponibles.')
        return redirect('home:home')
    
    # Crear objeto reserva temporal para mostrar contexto
    reserva = Reserva(
        cliente=request.user,
        vehiculo=vehiculo,
        fecha_recogida=datetime.datetime.fromisoformat(reserva_temporal['fecha_recogida']).date(),
        fecha_devolucion=datetime.datetime.fromisoformat(reserva_temporal['fecha_devolucion']).date(),
        costo_total=reserva_temporal['costo_total'],
        estado='PENDIENTE'
    )
    
    if request.method == 'POST':
        form = PagoForm(request.POST)
        if form.is_valid():
            # Procesar el pago
            resultado_pago = procesar_pago_tarjeta(
                numero_tarjeta=form.cleaned_data['numero_tarjeta'],
                nombre_titular=form.cleaned_data['nombre_titular'],
                mes_vencimiento=form.cleaned_data['mes_vencimiento'],
                ano_vencimiento=form.cleaned_data['ano_vencimiento'],
                cvv=form.cleaned_data['cvv'],
                monto=reserva_temporal['costo_total']
            )
            
            if resultado_pago['exito']:
                # Guardar información del pago en la sesión
                request.session['pago_procesado'] = {
                    'referencia_pago': resultado_pago['referencia_pago'],
                    'ultimos_4_digitos': resultado_pago['ultimos_4_digitos'],
                    'fecha_pago': resultado_pago['fecha_procesamiento'].isoformat(),
                    'monto': float(resultado_pago['monto_procesado'])
                }
                
                messages.success(request, '¡Pago procesado exitosamente!')
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
        form = PagoForm()
    
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
    
    if request.method == 'POST':
        # Verificar disponibilidad una vez más antes de guardar
        fecha_recogida = datetime.datetime.fromisoformat(reserva_temporal['fecha_recogida']).date()
        fecha_devolucion = datetime.datetime.fromisoformat(reserva_temporal['fecha_devolucion']).date()
        
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
            ultimos_4_digitos_tarjeta=pago_procesado['ultimos_4_digitos']
        )
        reserva.save()
        
        # Limpiar la sesión
        del request.session['reserva_temporal']
        del request.session['pago_procesado']
        
        # Mostrar página de confirmación exitosa
        return render(request, 'reservas/reserva_confirmada.html', {
            'reserva': reserva,
            'vehiculo': vehiculo
        })
    else:
        # Mostrar página de confirmación antes de procesar
        reserva = Reserva(
            cliente=request.user,
            vehiculo=vehiculo,
            fecha_recogida=datetime.datetime.fromisoformat(reserva_temporal['fecha_recogida']).date(),
            fecha_devolucion=datetime.datetime.fromisoformat(reserva_temporal['fecha_devolucion']).date(),
            costo_total=reserva_temporal['costo_total'],
            estado='PENDIENTE'
        )
        
        return render(request, 'reservas/confirmar_reserva_final.html', {
            'reserva': reserva,
            'vehiculo': vehiculo,
            'pago_procesado': pago_procesado
        })
