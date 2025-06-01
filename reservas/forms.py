from django import forms
from .models import Reserva
import datetime
import re

class ReservaForm(forms.ModelForm):

    fecha_recogida = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.date.today().isoformat()}),
        label="Fecha de Recogida"
    )
    fecha_devolucion = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'min': datetime.date.today().isoformat()}),
        label="Fecha de Devolución"
    )

    class Meta:
        model = Reserva

        fields = ['fecha_recogida', 'fecha_devolucion']

        labels = {
            'fecha_recogida': 'Fecha de Recogida',
            'fecha_devolucion': 'Fecha de Devolución',
        }

        help_texts = {
            'fecha_recogida': 'Formato: AAAA-MM-DD',
            'fecha_devolucion': 'Formato: AAAA-MM-DD',
        }

    def clean(self):

        cleaned_data = super().clean()
        fecha_recogida = cleaned_data.get('fecha_recogida')
        fecha_devolucion = cleaned_data.get('fecha_devolucion')

        if fecha_recogida and fecha_devolucion:
            if fecha_devolucion < fecha_recogida:
                self.add_error('fecha_devolucion', "La fecha de devolución no puede ser anterior a la fecha de recogida.")
            if fecha_recogida < datetime.date.today():
                self.add_error('fecha_recogida', "La fecha de recogida no puede ser anterior a la fecha actual.")
        return cleaned_data

class PagoForm(forms.Form):
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
        
        if mes and ano:
            fecha_vencimiento = datetime.date(int(ano), int(mes), 1)
            hoy = datetime.date.today().replace(day=1)
            
            if fecha_vencimiento < hoy:
                raise forms.ValidationError("La tarjeta está vencida.")
        
        return cleaned_data
