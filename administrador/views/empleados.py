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
from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin
from sucursales.models import Sucursal
from administrador.forms import EmpleadoModificarForm
import re


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
    sucursales = Sucursal.objects.all().order_by('nombre')
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        dni = request.POST.get('dni')
        email = request.POST.get('email')
        telefono = (request.POST.get('telefono') or '').strip()
        direccion = request.POST.get('direccion')
        sucursal_id = request.POST.get('sucursal')
        activo=True
        password = generate_random_password()

        if not re.fullmatch(r'\d{7,15}', telefono):
            messages.error(request, "El teléfono debe tener entre 7 y 15 dígitos, y solamente números")
            return render(request, 'administrador/cargar_empleados.html', {
                'request_post': request.POST,
                'sucursales': sucursales
            })

        if Empleado.objects.filter(dni=dni).exists():
            messages.error(request, "Ya existe un empleado con ese DNI.")
            return render(request, 'administrador/cargar_empleados.html', {
                'request_post': request.POST,
                'sucursales': sucursales
            })
        
        if Usuario.objects.filter(email=email).exists() or Empleado.objects.filter(email=email).exists():
            messages.error(request, "Ya existe un usuario o empleado con ese email.")
            return render(request, 'administrador/cargar_empleados.html', {
                'request_post': request.POST,
                'sucursales': sucursales
            })

        try:
            sucursal = get_object_or_404(Sucursal, id=sucursal_id) if sucursal_id else None

            # 1. Crear la cuenta de Usuario
            user = Usuario.objects.create_user(
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
                # --- ¡AQUÍ ESTÁ EL CAMBIO! ---
                is_staff=True, # <--- Establece is_staff en True para empleados
                # -----------------------------
            )
            
            # 2. Crear el perfil de Empleado y asociarlo al Usuario
            empleado = Empleado.objects.create(
                user=user,
                nombre=nombre,
                apellido=apellido,
                dni=dni,
                email=email,
                direccion=direccion,
                telefono=telefono,
                sucursal=sucursal
            )
            
            # 3. Enviar credenciales por email
            send_employee_credentials_email(request, email, password, f"{nombre} {apellido}")

            messages.success(request, f"Empleado {nombre} {apellido} cargado exitosamente. Credenciales creadas.")
            
            return redirect('admin_menu')
        
        except Exception as e:
            if 'user' in locals() and user.pk:
                user.delete()
            messages.error(request, f"Error al cargar el empleado: {e}")
            return render(request, 'administrador/cargar_empleados.html', {
                'request_post': request.POST,
                'sucursales': sucursales
            }) 
            
    return render(request, 'administrador/cargar_empleados.html', {'sucursales': sucursales})

@admin_required
def borrar_empleado(request):
    if request.method == 'POST':
        dni = request.POST.get('dni')
        empleado = get_object_or_404(Empleado, dni=dni)
        empleado.soft_delete()
        messages.success(request, f"El empleado {empleado.nombre} {empleado.apellido} ha sido dado de baja exitosamente.")
        return redirect('borrar_empleado')
    
    # Para GET, mostrar la lista de empleados
    mostrar_inactivos = request.GET.get('mostrar_inactivos', False)
    empleados = Empleado.objects.all()
    if not mostrar_inactivos:
        empleados = empleados.filter(activo=True)
    empleados = empleados.order_by('apellido', 'nombre')
    
    context = {
        'empleados': empleados,
        'mostrar_inactivos': mostrar_inactivos
    }
    return render(request, 'administrador/eliminar_empleado.html', context)

class ListarEmpleadosView(UserPassesTestMixin, ListView):
    model = Empleado
    template_name = 'administrador/listar_empleados.html'
    context_object_name = 'empleados'
    paginate_by = 10
    ordering = ['apellido', 'nombre']

    def test_func(self):
        return self.request.user.is_superuser

    def get_queryset(self):
        queryset = super().get_queryset()
        # Por defecto, mostrar solo empleados activos
        mostrar_inactivos = self.request.GET.get('mostrar_inactivos', False)
        if not mostrar_inactivos:
            queryset = queryset.filter(activo=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mostrar_inactivos'] = self.request.GET.get('mostrar_inactivos', False)
        return context

    def handle_no_permission(self):
        messages.error(self.request, "No tienes permisos para acceder a esta página.")
        return redirect('home:home')

def modificar_empleado(request):
    dni_seleccionado = request.GET.get("dni")
    empleado = None
    form = None

    if dni_seleccionado:
        try:
            empleado = Empleado.objects.get(dni=dni_seleccionado, activo=True)
        except Empleado.DoesNotExist:
            messages.error(request, "Empleado no encontrado o inactivo.")
            return redirect('modificar_empleado')  # redirige para limpiar la URL

    if request.method == "POST" and empleado:
        form = EmpleadoModificarForm(request.POST, instance=empleado)
        if form.is_valid():
            form.save()
            messages.success(request, "Empleado modificado correctamente.")
            return redirect(f"{request.path}?dni={empleado.dni}")
        else:
            messages.error(request, "Corrija los errores del formulario.")
    elif empleado:
        form = EmpleadoModificarForm(instance=empleado)

    empleados = Empleado.objects.filter(activo=True).order_by("apellido", "nombre")

    return render(request, "administrador/modificar_empleado.html", {
        "empleados": empleados,
        "empleado": empleado,
        "form": form,
    })