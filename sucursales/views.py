from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q
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

class VehiculoFiltradoListView(ListView):
    model = Vehiculo
    template_name = 'sucursales/vehiculo_filtrado_list.html'
    context_object_name = 'vehiculos'

    def get_queryset(self):
        queryset = Vehiculo.objects.filter(disponible=True)
        
        # Obtener parámetros de filtrado
        categoria = self.request.GET.get('categoria')
        capacidad = self.request.GET.get('capacidad')
        
        # Aplicar filtros
        if categoria:
            queryset = queryset.filter(tipo=categoria)
        if capacidad:
            queryset = queryset.filter(capacidad=capacidad)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todas las categorías disponibles
        context['categorias'] = dict(Vehiculo.TIPO_CHOICES)
        # Obtener todas las capacidades disponibles
        context['capacidades'] = Vehiculo.objects.filter(disponible=True).values_list('capacidad', flat=True).distinct().order_by('capacidad')
        # Mantener los valores de los filtros en el contexto
        context['categoria_seleccionada'] = self.request.GET.get('categoria', '')
        context['capacidad_seleccionada'] = self.request.GET.get('capacidad', '')
        return context