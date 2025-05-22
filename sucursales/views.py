from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import Sucursal
from vehiculos.models import Vehiculo

class SucursalListView(ListView):
    model = Sucursal
    template_name = 'sucursales/sucursal_list.html'
    context_object_name = 'sucursales'
    queryset = Sucursal.objects.all().prefetch_related('vehiculos_en_sucursal')



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