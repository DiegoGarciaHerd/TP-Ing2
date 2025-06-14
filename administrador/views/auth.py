import random
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.cache import cache
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from usuarios.models import Usuario
from django.utils import timezone
from datetime import timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from administrador.decorators import admin_required
from core.models import AdminBalance
from decimal import Decimal
from reservas.models import Reserva
from django.db.models import Sum, F

def generate_2fa_code():
    """Genera un código de 6 dígitos numérico"""
    return str(random.randint(100000, 999999))  # Rango 100000-999999

@never_cache
@csrf_protect
def login_admin_step1(request):
    if request.user.is_authenticated:
        logout(request)

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
      
        if user and user.is_admin:
            code = generate_2fa_code()   
            expiry = timezone.now() + timedelta(minutes=5)
            
            cache_data = {
                'code': code,  
                'user_id': user.pk,
                'expiry': expiry.timestamp(),
                'attempts': 3  
            }
            cache.set(f'admin_2fa_{user.pk}', cache_data, timeout=300)
            
            send_verification_email(user, code)  
            
            request.session['admin_2fa_user'] = user.pk
            return redirect('admin_login_step2')
        
        messages.error(request, "Credenciales inválidas o no tiene privilegios de administrador")
    return render(request, 'administrador/login_step1.html')

def send_verification_email(user, code):
    """Envía email con el código de 6 dígitos"""
    context = {
        'user': user,
        'code': code,  
        'expiry_minutes': 5,
        'app_name': 'AutoRental Admin'
    }
    
    email_html = render_to_string('administrador/admin_2fa.html', context)
    email_text = f"Hola {user.first_name},\n\nTu código de verificación es: {code}"
    
    email = EmailMultiAlternatives(
        subject='🔢 Tu Código de Acceso - Panel Administrativo',
        body=email_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.DEFAULT_FROM_EMAIL]
    )
    email.attach_alternative(email_html, "text/html")
    email.send()

@never_cache
@csrf_protect
def login_admin_step2(request):
    user_id = request.session.get('admin_2fa_user')
    if not user_id:
        return redirect('admin_login_step1')

    cached_data = cache.get(f'admin_2fa_{user_id}')
    if not cached_data:
        messages.error(request, "Solicitud expirada. Por favor inicie el proceso nuevamente.")
        return redirect('admin_login_step1')

    if request.method == 'POST':
        user_code = request.POST.get('code', '').strip()
        
        # Validaciones
        if not user_code or not user_code.isdigit() or len(user_code) != 6:
            messages.error(request, "Ingrese un código válido de 6 dígitos")
            return render(request, 'administrador/login_step2.html')
            
        if timezone.now().timestamp() > cached_data['expiry']:
            messages.error(request, "El código ha expirado")
            cache.delete(f'admin_2fa_{user_id}')
            return redirect('admin_login_step1')
            
        if cached_data['code'] == user_code:  
            user = Usuario.objects.get(pk=user_id)
            login(request, user)
            cache.delete(f'admin_2fa_{user_id}')
            return redirect('admin_menu')
        else:
            # Manejo de intentos fallidos
            cached_data['attempts'] -= 1
            cache.set(f'admin_2fa_{user_id}', cached_data, timeout=300)
            
            if cached_data['attempts'] <= 0:
                cache.delete(f'admin_2fa_{user_id}')
                messages.error(request, "Demasiados intentos fallidos. Por favor inicie nuevamente.")
                return redirect('admin_login_step1')
                
            messages.error(request, f"Código incorrecto. Intentos restantes: {cached_data['attempts']}")
    
    return render(request, 'administrador/login_step2.html')

def admin_logout(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('admin_login_step1')

@admin_required
def admin_menu(request):
    saldo_admin = Decimal('0.00') # Inicializa con Decimal para consistencia
    try:
        admin_balance, created = AdminBalance.objects.get_or_create(pk=1)
        saldo_admin = admin_balance.saldo
    except Exception as e:
        print(f"DEBUG: Error al obtener saldo del administrador: {e}") # Para depuración
        messages.error(request, f"Error al cargar el saldo del sistema: {e}")


    ingresos_confirmados = Reserva.objects.filter(
        estado='CONFIRMADA',

    ).aggregate(total=Sum('costo_total'))['total']


    reembolsos_cancelados = Reserva.objects.filter(
        estado='CANCELADA',
        monto_a_reembolsar__gt=0 # Solo las que tienen un monto a reembolsar positivo
    ).aggregate(total=Sum('monto_a_reembolsar'))['total']

  
    ingresos_confirmados = ingresos_confirmados if ingresos_confirmados is not None else Decimal('0.00')
    reembolsos_cancelados = reembolsos_cancelados if reembolsos_cancelados is not None else Decimal('0.00')

    total_ingresos = ingresos_confirmados + reembolsos_cancelados


    context = {
        'saldo_admin': saldo_admin,
        'total_ingresos': total_ingresos,
    }
    return render(request, 'administrador/menu_admin.html', context)