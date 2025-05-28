import random
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.core.cache import cache
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from usuarios.models import Usuario
from django.contrib.auth import logout
import secrets
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from vehiculos.models import Vehiculo
from empleados.models import Empleado


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

#---------------------------------AUTOS---------------------------------
#-----------------------------------------------------------------------

def cargar_autos(request):
    if request.method == 'POST':
        marca = request.POST.get('marca')
        modelo = request.POST.get('modelo')
        año = request.POST.get('año')
        patente = request.POST.get('patente')
        precio_por_dia = request.POST.get('precio')
        foto = request.POST.get('foto_base64')
        politica = request.POST.get('politica_reembolso')

        if Vehiculo.objects.filter(patente=patente).exists():
            messages.error(request, "Ya existe un vehículo con esa patente.")
            return render(request, 'administrador/cargar_autos.html')

        try:
            Vehiculo.objects.create(
                marca=marca,
                modelo=modelo,
                año=int(año),
                patente=patente,
                precio_por_dia=precio_por_dia,
                disponible=True,
                sucursal_actual_id=1,
                foto_base64=foto,
                politica_de_reembolso=politica
            )
            messages.success(request, "Autos cargados exitosamente")
        except Exception as e:
            messages.error(request, f"Error al cargar el auto: {e}")
            return render(request, 'administrador/cargar_autos.html')
        return redirect('admin_menu')
    return render(request, 'administrador/cargar_autos.html')

def borrar_autos(request):
    if request.method == 'POST':
        patente = request.POST.get('patente')
        
        try:
            vehiculo = Vehiculo.objects.get(patente=patente)
            vehiculo.delete()
            messages.success(request, "Auto borrado exitosamente")
        except Vehiculo.DoesNotExist:
            messages.error(request, "El auto a borrar no existe")
        except Exception as e:
            messages.error(request, f"Error al borrar el auto: {e}")
            return render(request, 'administrador/borrar_autos.html')
        return redirect('admin_menu')   
    return render(request, 'administrador/borrar_autos.html')

def modificar_autos(request):
    if request.method == 'POST':
        patente = request.POST.get('patente')

        try:
            vehiculo = Vehiculo.objects.get(patente=patente)

            precio = request.POST.get('precio')
            if precio:
                vehiculo.precio_por_dia = precio
            
            reembolso = request.POST.get('politica_reembolso')
            if reembolso:
                vehiculo.reembolso = reembolso

            politica = request.POST.get('politica_de_reembolso')
            if politica and politica != "Sin elegir":
                vehiculo.politica_de_reembolso = politica

            vehiculo.save()
            messages.success(request, "Autos modificados exitosamente")
            return redirect('admin_menu')  # Redirigir a la página de menú si se envía el formulario

        except Vehiculo.DoesNotExist:
            messages.error(request, "El auto a modificar no existe")
            return render(request, 'administrador/modificar_autos.html')
        
        except Exception as e:
            messages.error(request, f"Error al modificar el auto: {e}")
            return render(request, 'administrador/modificar_autos.html')

    return render(request, 'administrador/modificar_autos.html')

def ver_autos(request):
    vehiculos = Vehiculo.objects.all()
    return render(request, 'administrador/ver_autos.html', {'vehiculos': vehiculos})

#---------------------------------EMPLEADOS-----------------------------
#-----------------------------------------------------------------------

def cargar_empleados(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        direccion = request.POST.get('direccion')
        telefono = request.POST.get('telefono')
        
        try:
            Empleado.objects.create(
                nombre=nombre,
                direccion=direccion,
                telefono=telefono
            )
            messages.success(request, "Empleados cargados exitosamente")
        except Exception as e:
            messages.error(request, f"Error al cargar el empleado: {e}")
            return render(request, 'administrador/cargar_empleados.html')
        return redirect('admin_menu')
    return render(request, 'administrador/cargar_empleados.html')