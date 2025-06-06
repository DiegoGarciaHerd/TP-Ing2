from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import RegistroForm, EditarPerfilForm, CustomLoginForm, TarjetaGuardadaForm, CambiarPasswordForm
from .models import Usuario, TarjetaGuardada
import random
import string
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.views import LoginView
import secrets

Usuario = get_user_model()

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Iniciar sesión automáticamente después del registro
            messages.success(request, '¡Registro exitoso! Bienvenido/a a AutoRental.')
            return redirect('home:home')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


class UsuarioLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'usuarios/login.html'

    def form_valid(self, form):
        """Este método se llama si el formulario es válido."""
        user = form.get_user()
        if user.is_admin:
            form.add_error(None, ValidationError(
                "Los administradores deben usar el panel de administración.",
                code='admin_login_not_allowed'
            ))
            return self.form_invalid(form)

        login(self.request, user)  # Asegurarse de que el usuario esté logueado
        messages.success(self.request, f'¡Bienvenido/a {user.get_full_name() or user.email}!')
        return super().form_valid(form)

    def get_success_url(self):
        return '/admin/' if self.request.user.is_superuser else '/'

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('home:home')

@login_required
def editar_perfil(request):
    # Formulario de edición de perfil
    if request.method == 'POST':
        if 'cambiar_password' in request.POST:
            # Procesar cambio de contraseña
            form_password = CambiarPasswordForm(request.user, request.POST)
            if form_password.is_valid():
                form_password.save()
                messages.success(request, 'Tu contraseña ha sido actualizada correctamente.')
                return redirect('editar_perfil')
        else:
            # Procesar edición de perfil
            form_perfil = EditarPerfilForm(request.POST, instance=request.user)
            if form_perfil.is_valid():
                form_perfil.save()
                messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
                return redirect('editar_perfil')
    else:
        form_perfil = EditarPerfilForm(instance=request.user)
        form_password = CambiarPasswordForm(request.user)

    return render(request, 'usuarios/editar_perfil.html', {
        'form_perfil': form_perfil,
        'form_password': form_password
    })

@login_required
def gestionar_forma_pago(request):
    """Vista para mostrar y gestionar la tarjeta guardada del usuario"""
    tarjeta = None
    try:
        tarjeta = request.user.tarjeta_guardada
    except TarjetaGuardada.DoesNotExist:
        pass
    
    # Manejar eliminación de tarjeta
    if request.method == 'POST' and 'eliminar_tarjeta' in request.POST:
        if tarjeta:
            # Verificar si tiene reservas activas o pendientes
            if request.user.tiene_reservas_activas:
                messages.error(request, 
                              'No puedes eliminar tu tarjeta porque tienes reservas activas o pendientes. '
                              'La tarjeta se mantiene como garantía para posibles daños al vehículo o irregularidades en la reserva. '
                              'Puedes cambiarla por otra tarjeta nueva.')
            else:
                tarjeta.delete()
                messages.success(request, 'Tarjeta eliminada exitosamente.')
                tarjeta = None  # Actualizar la variable local
        else:
            messages.error(request, 'No tienes ninguna tarjeta guardada.')
        
        return redirect('gestionar_forma_pago')
    
    context = {
        'tarjeta': tarjeta,
        'tiene_reservas_activas': request.user.tiene_reservas_activas
    }
    return render(request, 'usuarios/gestionar_forma_pago.html', context)

@login_required
def agregar_tarjeta(request):
    """Vista para agregar o cambiar la tarjeta guardada"""
    if request.method == 'POST':
        form = TarjetaGuardadaForm(request.POST)
        if form.is_valid():
            # Crear nueva tarjeta (esto eliminará la anterior automáticamente)
            TarjetaGuardada.crear_tarjeta(
                usuario=request.user,
                numero_tarjeta=form.cleaned_data['numero_tarjeta'],
                nombre_titular=form.cleaned_data['nombre_titular'],
                mes_vencimiento=int(form.cleaned_data['mes_vencimiento']),
                ano_vencimiento=int(form.cleaned_data['ano_vencimiento'])
            )
            messages.success(request, 'Tarjeta guardada exitosamente.')
            return redirect('gestionar_forma_pago')
    else:
        form = TarjetaGuardadaForm()
    
    return render(request, 'usuarios/agregar_tarjeta.html', {'form': form})

def generate_random_password():
    """Genera una contraseña aleatoria de 8 caracteres con al menos una letra y un número"""
    # Asegurarse de que haya al menos una letra y un número
    password = [
        random.choice(string.ascii_letters),  # Una letra
        random.choice(string.digits),         # Un número
    ]
    # Completar hasta 8 caracteres con letras y números
    password.extend(random.choices(string.ascii_letters + string.digits, k=6))
    # Mezclar los caracteres
    random.shuffle(password)
    return ''.join(password)

def send_password_reset_email(user, new_password):
    """Envía email con la nueva contraseña"""
    try:
        context = {
            'user': user,
            'new_password': new_password,
        }
        
        email_html = render_to_string('usuarios/email_nueva_password.html', context)
        email_text = f"Hola {user.first_name},\n\nTu nueva contraseña es: {new_password}\n\nPor razones de seguridad, te recomendamos cambiar esta contraseña después de iniciar sesión."
        
        print(f"Intentando enviar correo a: {user.email}")
        print(f"Desde: {settings.DEFAULT_FROM_EMAIL}")
        print(f"Usando servidor: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        
        email = EmailMultiAlternatives(
            subject='🔑 Nueva Contraseña - AutoRental',
            body=email_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(email_html, "text/html")
        email.send()
        print("Correo enviado exitosamente")
        
    except Exception as e:
        print(f"Error al enviar el correo: {str(e)}")
        raise  # Re-lanzamos la excepción para que Django la maneje

def recuperar_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            usuario = Usuario.objects.get(email=email)
            
            # Generar nueva contraseña temporal
            nueva_password = generate_random_password()  # Usamos nuestra función que genera contraseñas más seguras
            usuario.set_password(nueva_password)
            usuario.save()
            
            try:
                # Enviar email con la nueva contraseña
                send_password_reset_email(usuario, nueva_password)
                messages.success(request, 
                               f'Se ha enviado una nueva contraseña a tu email: {email}. '
                               'Por favor, revisa tu bandeja de entrada.')
            except Exception as e:
                # Si falla el envío del correo, revertimos el cambio de contraseña
                usuario.set_password(usuario.password)  # Mantenemos la contraseña anterior
                usuario.save()
                messages.error(request, 
                             'Hubo un error al enviar el correo. Por favor, intenta nuevamente más tarde.')
                print(f"Error al enviar correo de recuperación: {str(e)}")
            
            return redirect('login')
            
        except Usuario.DoesNotExist:
            messages.error(request, 'No existe un usuario registrado con ese email.')
    
    return render(request, 'usuarios/recuperar_password.html')
