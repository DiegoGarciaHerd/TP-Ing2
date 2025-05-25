from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario
from django.core.exceptions import ValidationError

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    edad = forms.IntegerField(
        required=True, 
        min_value=18,
        help_text='Debe ser mayor de 18 años.'
    )
    DNI = forms.CharField(
        max_length=9, 
        required=True,
        help_text='Ingrese su número de DNI sin puntos.'
    )

    class Meta:
        model = Usuario
        fields = [
            'email',
            'first_name',
            'last_name',
            'edad',
            'DNI',
            'password1',
            'password2',
        ]
        labels = {
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'edad': 'Edad',
            'DNI': 'DNI',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'La contraseña debe tener al menos 5 caracteres, una letra y un dígito.'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self.fields['edad'].label = 'Edad'
        
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.edad = self.cleaned_data['edad']
        user.DNI = self.cleaned_data['DNI']
        if commit:
            user.save()
        return user

class EditarPerfilForm(UserChangeForm):
    password = None  # Elimina el campo de contraseña del formulario
    edad = forms.IntegerField(
        required=True,
        min_value=18,
        help_text='Debe ser mayor de 18 años.'
    )
    
    class Meta:
        model = Usuario
        fields = [
            'first_name',
            'last_name',
            'email',
            'edad',
            'DNI'
        ]
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
            'edad': 'Edad',
            'DNI': 'DNI',
        }

    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if edad < 18:
            raise ValidationError('Debe ser mayor de 18 años.')
        return edad

class CambiarRolForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['rol']
        labels = {
            'rol': 'Rol del usuario'
        }
