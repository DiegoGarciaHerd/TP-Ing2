from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Empleado
from sucursales.models import Sucursal

Usuario = get_user_model()

class EmpleadoEditarPerfilForm(forms.ModelForm):
    """Formulario para que los empleados editen su perfil"""
    
    # Campos del usuario asociado
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nombre'
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Apellido'
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Correo electrónico'
    )
    
    class Meta:
        model = Empleado
        fields = ['nombre', 'apellido', 'email', 'direccion', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Pre-llenar campos del usuario asociado
            user = self.instance.user
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Verificar que el email no esté en uso por otro usuario/empleado
            user_exists = Usuario.objects.filter(email=email).exclude(pk=self.instance.user.pk if self.instance.pk else None).exists()
            empleado_exists = Empleado.objects.filter(email=email).exclude(pk=self.instance.pk if self.instance.pk else None).exists()
            
            if user_exists or empleado_exists:
                raise ValidationError('Este email ya está en uso por otro usuario.')
        
        return email
    
    def save(self, commit=True):
        empleado = super().save(commit=False)
        
        # Actualizar también el usuario asociado
        if empleado.user:
            empleado.user.first_name = self.cleaned_data.get('first_name')
            empleado.user.last_name = self.cleaned_data.get('last_name')
            empleado.user.email = self.cleaned_data.get('email')
            if commit:
                empleado.user.save()
        
        if commit:
            empleado.save()
        
        return empleado

class EmpleadoCambiarPasswordForm(forms.Form):
    """Formulario para que los empleados cambien su contraseña"""
    
    password_actual = forms.CharField(
        label='Contraseña actual',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    password_nueva = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        help_text='La contraseña debe tener al menos 5 caracteres, una letra y un número.'
    )
    
    password_nueva_confirmacion = forms.CharField(
        label='Confirmar nueva contraseña',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password_actual(self):
        password_actual = self.cleaned_data.get('password_actual')
        if not self.user.check_password(password_actual):
            raise ValidationError('La contraseña actual es incorrecta.')
        return password_actual

    def clean_password_nueva(self):
        password = self.cleaned_data.get('password_nueva')
        if len(password) < 5:
            raise ValidationError('La contraseña debe tener al menos 5 caracteres.')
        
        if not any(c.isalpha() for c in password):
            raise ValidationError('La contraseña debe contener al menos una letra.')
            
        if not any(c.isdigit() for c in password):
            raise ValidationError('La contraseña debe contener al menos un número.')
            
        return password

    def clean_password_nueva_confirmacion(self):
        password_nueva = self.cleaned_data.get('password_nueva')
        password_nueva_confirmacion = self.cleaned_data.get('password_nueva_confirmacion')
        
        if password_nueva and password_nueva_confirmacion and password_nueva != password_nueva_confirmacion:
            raise ValidationError('Las contraseñas no coinciden.')
        
        return password_nueva_confirmacion

    def save(self):
        password_nueva = self.cleaned_data.get('password_nueva')
        self.user.set_password(password_nueva)
        self.user.save() 