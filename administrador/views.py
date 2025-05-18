from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from usuarios.models import Usuario
from django.http import HttpResponse
import random

TEMP_CODES = {} 

def login_admin_step1(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:  # Solo admins
            code = str(random.randint(100000, 999999))
            TEMP_CODES[username] = code 

            send_mail(
                'Código de verificación',
                f'Tu código es: {code}',
                'noreply@autorental.com',
                [user.email],
                fail_silently=False,
            )

            request.session['temp_user'] = username
            return redirect('admin_login_step2')
        else:
            messages.error(request, "Credenciales inválidas o no sos administrador.")
    return render(request, 'administrador/login_step1.html')


def login_admin_step2(request):
    username = request.session.get('temp_user')
    if not username:
        return redirect('admin_login_step1')

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        if TEMP_CODES.get(username) == codigo:
            from django.contrib.auth.models import User
            user = Usuario.objects.get(email=username)
            login(request, user)
            TEMP_CODES.pop(username, None)
            return redirect('admin_menu')
        else:
            messages.error(request, "Código inválido.")
    return render(request, 'administrador/login_step2.html')

def admin_menu(request):
    return render(request, 'administrador/menu_admin.html')