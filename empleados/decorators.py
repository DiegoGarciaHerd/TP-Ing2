from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

def empleado_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
            return redirect(reverse('login'))
        
        # Verificar que el usuario sea staff (empleado)
        if not request.user.is_staff:
            messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
            return redirect(reverse('home:home'))
        
        # Verificar que tenga perfil de empleado activo
        try:
            if hasattr(request.user, 'empleado_profile') and request.user.empleado_profile.activo:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
                return redirect(reverse('home:home'))
        except Exception as e:
            messages.error(request, "Ocurrió un error de permisos. Por favor, inténtalo de nuevo.")
            return redirect(reverse('home:home'))
    
    return wrapper