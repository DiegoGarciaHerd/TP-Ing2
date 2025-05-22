from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
import datetime

from .models import Reserva
from sucursales.models import Sucursal 
from vehiculos.models import Vehiculo
from .forms import ReservaForm




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
            reserva = form.save(commit=False) 
            reserva.cliente = request.user 
            reserva.vehiculo = vehiculo

            reservas_existentes = Reserva.objects.filter(
                vehiculo=vehiculo,
                fecha_recogida__lt=reserva.fecha_devolucion, 
                fecha_devolucion__gt=reserva.fecha_recogida, 
                estado__in=['PENDIENTE', 'CONFIRMADA'] 
            ).exclude(pk=reserva.pk) 

            if reservas_existentes.exists():
                messages.error(request, 'El vehículo ya está reservado para el período seleccionado. Por favor, elige otras fechas.')
                return render(request, 'reservas/crear_reserva.html', {'form': form, 'vehiculo': vehiculo})

            reserva.save() 
            messages.success(request, '¡Reserva creada con éxito!')
            return redirect('reservas:mis_reservas') 
    else:
        form = ReservaForm()
    return render(request, 'reservas/crear_reserva.html', {'form': form, 'vehiculo': vehiculo})


@login_required
def mis_reservas(request):
    reservas = Reserva.objects.filter(cliente=request.user).order_by('-fecha_creacion')
    return render(request, 'reservas/mis_reservas.html', {'reservas': reservas})


@login_required
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, cliente=request.user)
    return render(request, 'reservas/detalle_reserva.html', {'reserva': reserva})


@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, cliente=request.user)

    if reserva.estado in ['PENDIENTE', 'CONFIRMADA'] and reserva.fecha_recogida >= datetime.date.today():
        if request.method == 'POST':
            reserva.estado = 'CANCELADA'
            reserva.save()

            messages.success(request, 'Reserva cancelada exitosamente.')
            return redirect('reservas:mis_reservas')
        return render(request, 'reservas/confirmar_cancelacion.html', {'reserva': reserva})
    else:
        messages.error(request, 'No se puede cancelar esta reserva.')
        return redirect('reservas:mis_reservas')
