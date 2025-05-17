from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
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
