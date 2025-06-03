from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from .validators import validar_edad, validar_dni
import re
import datetime

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        help_text='Requerido. Ingrese una dirección de email válida.'
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Requerido.'
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Requerido.'
    )
    
    edad = forms.IntegerField(
        validators=[validar_edad],
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='Debe ser mayor de 18 años para registrarse.'
    )
    
    DNI = forms.CharField(
        max_length=10,
        validators=[validar_dni],
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Ingrese su DNI sin puntos ni espacios.'
    )

    class Meta:
        model = Usuario
        fields = ('email', 'first_name', 'last_name', 'edad', 'DNI', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.edad = self.cleaned_data['edad']
        user.DNI = self.cleaned_data['DNI']
        if commit:
            user.save()
        return user
    
class CustomLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        print("Intento de login con rol:", user.rol)
        if user.is_admin:
            print("Bloqueado: admin")
            raise ValidationError("Correo electrónico o contraseña incorrectos.")

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    def clean_edad(self):
        edad = self.cleaned_data.get('edad')
        if edad and edad < 18:
            raise ValidationError('Debe ser mayor de 18 años.')
        return edad

    def clean_DNI(self):
        dni = self.cleaned_data.get('DNI')
        if dni:
            validar_dni(dni)
        return dni

class CambiarRolForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['rol']
        labels = {
            'rol': 'Rol del usuario'
        }

class RecuperarPasswordForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tu email registrado'
        }),
        label='Email'
    )

class TarjetaGuardadaForm(forms.Form):
    numero_tarjeta = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'id': 'numero_tarjeta'
        }),
        label='Número de Tarjeta'
    )
    
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre como aparece en la tarjeta',
            'style': 'text-transform: uppercase;'
        }),
        label='Nombre del Titular'
    )
    
    mes_vencimiento = forms.ChoiceField(
        choices=[(i, f'{i:02d}') for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mes'
    )
    
    ano_vencimiento = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(datetime.date.today().year, datetime.date.today().year + 11)],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Año'
    )
    
    cvv = forms.CharField(
        max_length=4,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '123',
            'maxlength': '4'
        }),
        label='CVV'
    )

    def clean_numero_tarjeta(self):
        numero = self.cleaned_data['numero_tarjeta']
        # Eliminar espacios y guiones
        numero = re.sub(r'[\s-]', '', numero)
        
        # Verificar que solo contenga dígitos
        if not numero.isdigit():
            raise forms.ValidationError("El número de tarjeta debe contener solo dígitos.")
        
        # Verificar longitud (13-19 dígitos para la mayoría de tarjetas)
        if len(numero) < 13 or len(numero) > 19:
            raise forms.ValidationError("El número de tarjeta debe tener entre 13 y 19 dígitos.")
        
        # Algoritmo de Luhn básico para validación
        def luhn_check(card_num):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10 == 0
        
        if not luhn_check(numero):
            raise forms.ValidationError("El número de tarjeta no es válido.")
        
        return numero

    def clean_cvv(self):
        cvv = self.cleaned_data['cvv']
        if not cvv.isdigit():
            raise forms.ValidationError("El CVV debe contener solo dígitos.")
        if len(cvv) < 3 or len(cvv) > 4:
            raise forms.ValidationError("El CVV debe tener 3 o 4 dígitos.")
        return cvv

    def clean(self):
        cleaned_data = super().clean()
        mes = cleaned_data.get('mes_vencimiento')
        ano = cleaned_data.get('ano_vencimiento')
        numero_tarjeta = cleaned_data.get('numero_tarjeta')
        cvv = cleaned_data.get('cvv')
        nombre_titular = cleaned_data.get('nombre_titular')
        
        if mes and ano:
            fecha_vencimiento = datetime.date(int(ano), int(mes), 1)
            hoy = datetime.date.today().replace(day=1)
            
            if fecha_vencimiento < hoy:
                raise forms.ValidationError("La tarjeta está vencida.")
        
        # Validación de tarjetas permitidas (hardcodeadas)
        if numero_tarjeta and cvv and nombre_titular and mes and ano:
            # Limpiar número de tarjeta (eliminar espacios y guiones)
            numero_limpio = re.sub(r'[\s-]', '', numero_tarjeta)
            
            # Tarjetas permitidas
            tarjetas_permitidas = [
                {
                    'numero': '4517660196851645',
                    'mes': '8',
                    'ano': '2030',
                    'cvv': '456',
                    'nombre': 'CONRADO FEDERICO ESCOBARES'
                },
                {
                    'numero': '5258556802017961',
                    'mes': '8',
                    'ano': '2029',
                    'cvv': '789',
                    'nombre': 'ESCOBARES CONRADO F'
                },
                {
                    'numero': '4532015112830366',
                    'mes': '10',
                    'ano': '2030',
                    'cvv': '123',
                    'nombre': 'JUAN PEREZ'
                }
            ]
            
            # Verificar si la tarjeta coincide con alguna permitida
            tarjeta_valida = False
            tarjeta_sin_fondos = False
            
            for tarjeta in tarjetas_permitidas:
                if (numero_limpio == tarjeta['numero'] and
                    str(mes) == tarjeta['mes'] and
                    str(ano) == tarjeta['ano'] and
                    cvv == tarjeta['cvv'] and
                    nombre_titular.upper() == tarjeta['nombre']):
                    tarjeta_valida = True
                    # Verificar si es la tarjeta sin fondos
                    if numero_limpio == '4532015112830366':
                        tarjeta_sin_fondos = True
                    break
            
            if not tarjeta_valida:
                raise forms.ValidationError("Los datos de la tarjeta no coinciden con una tarjeta autorizada.")
            
            if tarjeta_sin_fondos:
                raise forms.ValidationError("La tarjeta no tiene fondos suficientes para realizar el pago.")
        
        return cleaned_data
