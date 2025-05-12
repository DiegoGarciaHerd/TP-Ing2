from django.shortcuts import render
from django.http import HttpResponse

def lista_vehiculos(request):
      return HttpResponse("Aquí se listarán los vehículos.")

def detalle_vehiculo(request, pk):
    return HttpResponse(f"Detalles del vehículo con ID: {pk}")