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