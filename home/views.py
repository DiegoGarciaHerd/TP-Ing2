from django.shortcuts import render
from sucursales.models import Sucursal

# Create your views here.

def home(request):
    sucursales = Sucursal.objects.all()
    return render(request, 'home/home.html', {'sucursales': sucursales})
