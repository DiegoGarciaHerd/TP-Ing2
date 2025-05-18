from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistroForm, EditarPerfilForm

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Te has registrado correctamente! Ya puedes acceder a tu cuenta.')
            return redirect('home')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido/a {user.get_full_name() or user.email}! Has iniciado sesión correctamente.')
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'usuarios/login.html', {'form': form})
