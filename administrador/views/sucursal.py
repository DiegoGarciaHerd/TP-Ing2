# D:\Tp IS2\TP-Ing2\administrador\views\sucursal.py
import random
import string
from django.shortcuts import render, redirect
from django.contrib import messages
from administrador.decorators import admin_required1
from django.conf import settings

def cargar_sucursal(request):
    return render(request, 'administrador/cargar_sucursal.html')