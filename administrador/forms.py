from django.core.exceptions import ValidationError
import re
from django import forms
from empleados.models import Empleado
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class EmpleadoModificarForm(forms.ModelForm):
    class Meta:
        model = Empleado
        fields = ['nombre', 'apellido', 'email', 'direccion', 'telefono', 'sucursal']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'sucursal': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        
        if not email:
            raise ValidationError("El email es requerido.")
        
        # Verificar si el email ya está siendo usado por otro usuario (cliente o empleado)
        if Usuario.objects.filter(email__iexact=email).exclude(id=self.instance.user.id if self.instance and self.instance.user else None).exists():
            raise ValidationError("Este email ya está siendo usado por otro usuario del sistema.")
        
        # Verificar si el email ya está siendo usado por otro empleado
        if Empleado.objects.filter(email__iexact=email).exclude(id=self.instance.id if self.instance else None).exists():
            raise ValidationError("Este email ya está siendo usado por otro empleado.")
        
        return email

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()

        if not telefono.isdigit():
            raise ValidationError("El teléfono debe contener solo números.")
        
        if not (7 <= len(telefono) <= 15):
            raise ValidationError("El teléfono debe tener entre 7 y 15 dígitos.")
        
        return telefono