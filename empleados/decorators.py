# decorators.py
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from functools import wraps

def empleado_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print("\n--- INICIO DECORADOR empleado_required ---")
        print(f"URL accedida: {request.path}")
        print(f"Usuario autenticado: {request.user.is_authenticated}")

        if not request.user.is_authenticated:
            print("FALLO: Usuario no autenticado.")
            messages.error(request, "Debes iniciar sesión para acceder a esta sección.")
            return redirect(reverse('usuarios:login')) # Asegúrate que 'usuarios:login' es correcto

        print(f"Usuario: {request.user.username}")
        print(f"Usuario es staff: {request.user.is_staff}")

        if not request.user.is_staff:
            print("FALLO: Usuario no es staff.")
            messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
            return redirect(reverse('home:home')) # Redirige a la página de inicio

        # Verificar que tenga perfil de empleado activo
        try:
            has_profile = hasattr(request.user, 'empleado_profile')
            print(f"Usuario tiene empleado_profile: {has_profile}")

            if has_profile:
                profile_activo = request.user.empleado_profile.activo
                print(f"EmpleadoProfile activo: {profile_activo}")
                if profile_activo:
                    print("ÉXITO: Todas las condiciones de empleado cumplidas.")
                    return view_func(request, *args, **kwargs)
                else:
                    print("FALLO: EmpleadoProfile no activo.")
                    messages.error(request, "Tu perfil de empleado no está activo o no se encontró.")
                    return redirect(reverse('home:home'))
            else:
                print("FALLO: No se encontró empleado_profile.")
                messages.error(request, "No tienes permisos de empleado para acceder a esta sección.")
                return redirect(reverse('home:home'))

        except Exception as e:
            print(f"¡EXCEPCIÓN EN DECORADOR! Error: {e}")
            messages.error(request, "Ocurrió un error de permisos. Por favor, inténtalo de nuevo.")
            return redirect(reverse('home:home'))

    return wrapper