from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Vehiculo

def lista_vehiculos(request):
    vehiculos = Vehiculo.objects.all()
    return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

def detalle_vehiculo(request, pk):
    vehiculo = get_object_or_404(Vehiculo, pk=pk)
    return render(request, 'sucursales/vehiculo_detail.html', {'vehiculo': vehiculo})