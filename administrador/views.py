import random
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.core.cache import cache
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from usuarios.models import Usuario


@never_cache
@csrf_protect
def login_admin_step1(request):
   

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
      
        if user and user.is_admin:
            code = str(random.randint(100000, 999999))
            cache.set(f'admin_2fa_{user.pk}', code, timeout=300)
            
            send_mail(
                'Código de verificación',
                f'Tu código es: {code}',
                'noreply@autorental.com',
                [user.email],
                fail_silently=False,
            )
            request.session['admin_2fa_user'] = user.pk
            return redirect('admin_login_step2')
        
        messages.error(request, "Credenciales inválidas o no tiene privilegios de administrador")
    return render(request, 'administrador/login_step1.html')

@never_cache
@csrf_protect
def login_admin_step2(request):
    user_id = request.session.get('admin_2fa_user')
    if not user_id:
        return redirect('admin_login_step1')

    if request.method == 'POST':
        codigo = request.POST.get('codigo')
        cached_code = cache.get(f'admin_2fa_{user_id}')
        
        if cached_code and cached_code == codigo:
            user = Usuario.objects.get(pk=user_id)
            login(request, user)
            cache.delete(f'admin_2fa_{user_id}')
            return redirect('admin_menu')
        
        messages.error(request, "Código inválido o expirado")
    return render(request, 'administrador/login_step2.html')

from django.contrib.auth.decorators import login_required, user_passes_test

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('admin_login_step1')
            
        if not (request.user.is_active and request.user.is_staff and request.user.is_superuser):
            messages.error(request, "No tienes permisos de administrador")
            return redirect('admin_login_step1')
            
        return view_func(request, *args, **kwargs)
    return wrapper

@admin_required
def admin_menu(request):
    return render(request, 'administrador/menu_admin.html')

def cargar_autos(request):
    return render(request, 'administrador/cargar_autos.html')