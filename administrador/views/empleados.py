# D:\Tp IS2\TP-Ing2\administrador\views\empleados.py

import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from empleados.models import Empleado
from administrador.decorators import admin_required
from django.contrib.auth import get_user_model 
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
from ..forms import ModificarEmpleadoForm
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin

Usuario = get_user_model() 


def generate_random_password(length=12):
    if length < 5:
        length = 5 

    password_characters = [
        random.choice(string.ascii_letters), 
        random.choice(string.digits)        
    ]
    

    all_characters = string.ascii_letters + string.digits + string.punctuation
    
    remaining_length = length - len(password_characters)
    password_characters.extend(random.choice(all_characters) for _ in range(remaining_length))
    
    random.shuffle(password_characters) 
    
    return ''.join(password_characters)

def send_employee_credentials_email(request, user_email, password, employee_name): 
    context = {
        'employee_name': employee_name,
        'email': user_email,
        'password': password,
    }
    email_html = render_to_string('administrador/email_empleado_credenciales.html', context)
    email_text = f"Hola {employee_name},\n\n" \
                 f"Tus credenciales para acceder al sistema son:\n" \
                 f"Email: {user_email}\n" \
                 f"Contraseña: {password}\n\n" \
                 f"Por razones de seguridad, te recomendamos cambiar tu contraseña al iniciar sesión por primera vez."

    email = EmailMultiAlternatives(
        subject='Credenciales de Acceso a AutoRental',
        body=email_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email]
    )
    email.attach_alternative(email_html, "text/html")
    try:
        email.send()
        messages.info(request, f"Credenciales enviadas a {user_email}") 
    except Exception as e:
        messages.error(request, f"Error al enviar email a {user_email}: {e}")

@admin_required
def cargar_empleados(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        dni = request.POST.get('dni')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion') 

        # Generar una contraseña para el nuevo empleado
        password = generate_random_password()

        # Validaciones de unicidad (ahora para el modelo Usuario también)
        if Empleado.objects.filter(dni=dni).exists():
            messages.error(request, "Ya existe un empleado con ese DNI.")
            return render(request, 'administrador/cargar_empleados.html', {'request_post': request.POST}) # Puedes pasar los datos POST para rellenar el formulario
        
        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Ya existe un usuario con ese Email.")
            return render(request, 'administrador/cargar_empleados.html', {'request_post': request.POST}) # Puedes pasar los datos POST para rellenar el formulario

        try:
            # 1. Crear la cuenta de Usuario
            user = Usuario.objects.create_user(
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
            )
            
            # 2. Crear el perfil de Empleado y asociarlo al Usuario
            empleado = Empleado.objects.create(
                user=user,
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                email=email,
                direccion=direccion, # Usar la variable 'direccion' obtenida del POST
                telefono=telefono
            )
            
            # 3. Enviar credenciales por email
            send_employee_credentials_email(request, email, password, f"{nombre} {apellido}") # <-- PASAR 'request' AQUÍ

            messages.success(request, f"Empleado {nombre} {apellido} cargado exitosamente. Credenciales creadas.")
            
            return redirect('admin_menu')
        
        except Exception as e:
            if 'user' in locals() and user.pk:
                user.delete()
            messages.error(request, f"Error al cargar el empleado: {e}")
            # Si hay un error, volvemos a renderizar el formulario con los datos para que no los pierda
            return render(request, 'administrador/cargar_empleados.html', {'request_post': request.POST}) 
            
    # Para el método GET, renderizamos el formulario vacío
    return render(request, 'administrador/cargar_empleados.html')

@admin_required
def modificar_empleados(request):
    if request.method == 'POST':
        # Si hay un DNI en el POST, obtener el empleado y usarlo como instancia
        dni = request.POST.get('dni')
        empleado = get_object_or_404(Empleado, dni=dni) if dni else None
        form = ModificarEmpleadoForm(request.POST, instance=empleado)
        
        if form.is_valid():
            empleado = form.save(commit=False)
            user = empleado.user
            
            # Actualizar también el usuario asociado
            user.first_name = empleado.nombre
            user.last_name = empleado.apellido
            user.email = empleado.email
            
            try:
                user.save()
                empleado.save()
                messages.success(request, f"Empleado {empleado.nombre} {empleado.apellido} modificado exitosamente")
                return redirect('admin_menu')
            except Exception as e:
                messages.error(request, f"Error al modificar el empleado: {e}")
    else:
        # Si hay un DNI en el GET, pre-seleccionar ese empleado
        dni = request.GET.get('dni')
        empleado = get_object_or_404(Empleado, dni=dni) if dni else None
        form = ModificarEmpleadoForm(instance=empleado)

    return render(request, 'administrador/modificar_empleados.html', {'form': form})

class ListarEmpleadosView(UserPassesTestMixin, ListView):
    model = Empleado
    template_name = 'administrador/listar_empleados.html'
    context_object_name = 'empleados'
    paginate_by = 10  # Número de empleados por página
    ordering = ['apellido', 'nombre']  # Ordenar por apellido y nombre

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('home:home')