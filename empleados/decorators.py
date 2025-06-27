"""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse # Importa reverse

def empleado_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
            return redirect(reverse('login')) # Redirige a tu URL de login general
        
        # Intentar acceder al perfil de empleado, si existe y está activo
        try:
            if request.user.is_staff and request.user.empleado_profile.activo:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
                return redirect(reverse('home:home')) # Redirige a la página principal si no es empleado
        except Exception: # Si el usuario no tiene un perfil de empleado (es un cliente o superuser sin perfil de empleado)
            messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
            return redirect(reverse('home:home')) # Redirige a la página principal
    return wrapper
"""
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

def empleado_required(view_func):
    def wrapper(request, *args, **kwargs):
        print(f"DEBUG DECORADOR - Vista: {view_func.__name__}")
        print(f"DEBUG DECORADOR - User autenticado: {request.user.is_authenticated}")
        if request.user.is_authenticated:
            print(f"DEBUG DECORADOR - User: {request.user.username}, is_staff: {request.user.is_staff}")
        else:
            messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
            return redirect(reverse('login')) 
        
        try:
            # Primero, asegurate de que el atributo empleado_profile exista antes de intentar acceder a él
            if hasattr(request.user, 'empleado_profile'):
                print(f"DEBUG DECORADOR - Empleado_profile existe para {request.user.username}.")
                print(f"DEBUG DECORADOR - Empleado_profile.activo: {request.user.empleado_profile.activo}")

                if request.user.is_staff and request.user.empleado_profile.activo:
                    print(f"DEBUG DECORADOR - Permiso CONCEDIDO para {request.user.username}.")
                    return view_func(request, *args, **kwargs)
                else:
                    print(f"DEBUG DECORADOR - Permiso DENEGADO por is_staff o activo false para {request.user.username}.")
                    messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
                    return redirect(reverse('login'))
            else:
                print(f"DEBUG DECORADOR - Usuario {request.user.username} NO tiene un empleado_profile asociado.")
                messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
                return redirect(reverse('login'))
        except Exception as e:
            print(f"DEBUG DECORADOR - ¡Excepción INESPERADA en decorador!: {e}")
            messages.error(request, "Ocurrió un error de permisos. Por favor, inténtalo de nuevo.")
            return redirect(reverse('login'))
    return wrapper