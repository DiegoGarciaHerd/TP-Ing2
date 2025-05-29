from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from .forms import RegistroForm, EditarPerfilForm, CustomLoginForm
from .models import Usuario
import random
import string
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.views import LoginView

Usuario = get_user_model()

def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Te has registrado correctamente! Ya puedes acceder a tu cuenta.')
            return redirect('home:home')
    else:
        form = RegistroForm()
    return render(request, 'usuarios/registro.html', {'form': form})


class UsuarioLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'usuarios/login.html'

    def form_valid(self, form):
        """Este método se llama si el formulario es válido. Redireccionamos manualmente."""
        user = form.get_user()
        if user.is_admin:
            form.add_error(None, ValidationError(
                "Los administradores deben usar el panel de administración.",
                code='admin_login_not_allowed'
            ))
            return self.form_invalid(form)

        messages.success(self.request, f'¡Bienvenido/a {user.get_full_name() or user.email}!')
        return super().form_valid(form)

    def get_success_url(self):
        return '/'  # Redirige a la página principal

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, 'Has cerrado sesión correctamente.')
    return redirect('home:home')

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect('editar_perfil')
    else:
        form = EditarPerfilForm(instance=request.user)
    return render(request, 'usuarios/editar_perfil.html', {'form': form})

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
            user = Usuario.objects.get(email=email)
            if user.is_admin:
                messages.error(request, 'Esta función no está disponible para administradores.')
                return render(request, 'usuarios/recuperar_password.html')
            
            # Generar nueva contraseña
            new_password = generate_random_password()
            
            # Actualizar la contraseña del usuario
            user.set_password(new_password)
            user.save()
            
            # Enviar email con la nueva contraseña
            send_password_reset_email(user, new_password)
            
            messages.success(request, 'Se ha enviado una nueva contraseña a tu correo electrónico.')
            return redirect('login')
            
        except Usuario.DoesNotExist:
            # Por seguridad, mostramos el mismo mensaje aunque el usuario no exista
            messages.success(request, 'Si el correo existe en nuestra base de datos, recibirás una nueva contraseña.')
            return redirect('login')
            
    return render(request, 'usuarios/recuperar_password.html')
