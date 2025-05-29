from django.contrib import messages
from django.shortcuts import redirect

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            messages.error(request, "No tienes permisos de administrador")
            return redirect('admin_login_step1')
        return view_func(request, *args, **kwargs)
    return wrapper 