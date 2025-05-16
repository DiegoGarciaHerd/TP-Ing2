from django.shortcuts import render
from django.http import HttpResponse
from .models import Vehiculo

def lista_vehiculos(request):
      vehiculos = Vehiculo.objects.all()
      return render(request, 'vehiculos/lista_vehiculos.html', {'vehiculos': vehiculos})

def detalle_vehiculo(request, pk):
    return HttpResponse(f"Detalles del vehículo con ID: {pk}")