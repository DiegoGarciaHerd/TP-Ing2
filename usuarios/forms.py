from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

class RegistroForm(UserCreationForm):
    email = forms.EmailField(required=True)
    telefono = forms.CharField(max_length=20, required=False)
    direccion = forms.CharField(widget=forms.Textarea, required=False)
    
    class Meta:
        model = Usuario
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'telefono',
            'direccion',
            'password1',
            'password2'
        ]
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'first_name': 'Nombre',
            'last_name': 'Apellido',
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.telefono = self.cleaned_data['telefono']
        user.direccion = self.cleaned_data['direccion']
        if commit:
            user.save()
        return user

class EditarPerfilForm(UserChangeForm):
    password = None  # Elimina el campo de contraseña del formulario
    
    class Meta:
        model = Usuario
        fields = [
            'first_name',
            'last_name',
            'email',
            'telefono',
            'direccion'
        ]
        labels = {
            'first_name': 'Nombre',
            'last_name': 'Apellido',
            'email': 'Correo electrónico',
        }

class CambiarRolForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['rol']
        labels = {
            'rol': 'Rol del usuario'
        }