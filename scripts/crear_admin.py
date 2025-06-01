import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autorental.settings")
django.setup()

from usuarios.models import Usuario

if not Usuario.objects.filter(email='admin@autorental.com').exists():
    admin = Usuario.objects.create_superuser(
        email='admin@autorental.com',
        password='fghrty456',
        first_name='Admin',  # Estos campos son requeridos al crear superusuario
        last_name='Usuario'
    )
    admin.is_staff = True
    #admin.is_superuser = True
    admin.save()
    print("Admin creado")
else:
    print("Admin ya existe")