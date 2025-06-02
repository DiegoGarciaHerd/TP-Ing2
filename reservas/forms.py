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
    conductor_nombre = forms.CharField(label="Nombre del Conductor", max_length=100)
    conductor_apellido = forms.CharField(label="Apellido del Conductor", max_length=100)
    conductor_dni = forms.CharField(label="DNI del Conductor", max_length=20)

    class Meta:
        model = Reserva
        fields = ['fecha_recogida', 'fecha_devolucion', 'conductor_nombre', 'conductor_apellido', 'conductor_dni']
        labels = {
            'fecha_recogida': 'Fecha de Recogida',
            'fecha_devolucion': 'Fecha de Devolución',
            'conductor_nombre': 'Nombre del Conductor',
            'conductor_apellido': 'Apellido del Conductor',
            'conductor_dni': 'DNI del Conductor',
        }
        help_texts = {
            'fecha_recogida': 'Formato: AAAA-MM-DD',
            'fecha_devolucion': 'Formato: AAAA-MM-DD',
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_recogida = cleaned_data.get('fecha_recogida')
        fecha_devolucion = cleaned_data.get('fecha_devolucion')
        dni = cleaned_data.get('conductor_dni')

        if fecha_recogida and fecha_devolucion:
            if fecha_devolucion < fecha_recogida:
                self.add_error('fecha_devolucion', "La fecha de devolución no puede ser anterior a la fecha de recogida.")
            if fecha_recogida < datetime.date.today():
                self.add_error('fecha_recogida', "La fecha de recogida no puede ser anterior a la fecha actual.")

        # Validar que el DNI no esté en otra reserva activa
        if dni and fecha_recogida and fecha_devolucion:
            from .models import Reserva
            reservas_existentes = Reserva.objects.filter(
                conductor_dni=dni,
                fecha_recogida__lt=fecha_devolucion,
                fecha_devolucion__gt=fecha_recogida,
                estado__in=['PENDIENTE', 'CONFIRMADA']
            )
            if reservas_existentes.exists():
                self.add_error('conductor_dni', "Este DNI ya está asignado a otra reserva activa en las fechas seleccionadas.")
        return cleaned_data

class CrearReservaForm(forms.ModelForm):
    fecha_recogida = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    fecha_devolucion = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    class Meta:
        model = Reserva
        fields = ['fecha_recogida', 'fecha_devolucion']
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_recogida = cleaned_data.get('fecha_recogida')
        fecha_devolucion = cleaned_data.get('fecha_devolucion')
        
        if fecha_recogida and fecha_devolucion:
            if fecha_devolucion <= fecha_recogida:
                raise forms.ValidationError("La fecha de devolución debe ser posterior a la fecha de recogida.")
        
        return cleaned_data

class PagoForm(forms.Form):
    usar_tarjeta_guardada = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Usar mi tarjeta guardada'
    )
    
    numero_tarjeta = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '1234 5678 9012 3456',
            'id': 'numero_tarjeta'
        }),
        label='Número de Tarjeta',
        required=False
    )
    
    nombre_titular = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre como aparece en la tarjeta',
            'style': 'text-transform: uppercase;'
        }),
        label='Nombre del Titular',
        required=False
    )
    
    mes_vencimiento = forms.ChoiceField(
        choices=[(i, f'{i:02d}') for i in range(1, 13)],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Mes',
        required=False
    )
    
    ano_vencimiento = forms.ChoiceField(
        choices=[(i, str(i)) for i in range(datetime.date.today().year, datetime.date.today().year + 11)],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Año',
        required=False
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

    def __init__(self, *args, **kwargs):
        self.usuario = kwargs.pop('usuario', None)
        super().__init__(*args, **kwargs)
        
        # Si el usuario tiene tarjeta guardada, mostrar la opción
        if self.usuario and hasattr(self.usuario, 'tarjeta_guardada'):
            try:
                tarjeta = self.usuario.tarjeta_guardada
                self.fields['usar_tarjeta_guardada'].label = f'Usar tarjeta terminada en {tarjeta.ultimos_4_digitos}'
            except:
                # Si no tiene tarjeta guardada, ocultar la opción
                del self.fields['usar_tarjeta_guardada']
        else:
            del self.fields['usar_tarjeta_guardada']

    def clean_numero_tarjeta(self):
        numero = self.cleaned_data.get('numero_tarjeta', '')
        usar_guardada = self.cleaned_data.get('usar_tarjeta_guardada', False)
        
        if usar_guardada:
            return numero  # No validar si usa tarjeta guardada
        
        if not numero:
            raise forms.ValidationError("El número de tarjeta es requerido.")
            
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
    
    def clean_nombre_titular(self):
        nombre = self.cleaned_data.get('nombre_titular', '')
        usar_guardada = self.cleaned_data.get('usar_tarjeta_guardada', False)
        
        if usar_guardada:
            return nombre
            
        if not nombre:
            raise forms.ValidationError("El nombre del titular es requerido.")
        return nombre

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv', '')
        if not cvv:
            raise forms.ValidationError("El CVV es requerido.")
            
        if not cvv.isdigit():
            raise forms.ValidationError("El CVV debe contener solo dígitos.")
        if len(cvv) < 3 or len(cvv) > 4:
            raise forms.ValidationError("El CVV debe tener 3 o 4 dígitos.")
        return cvv

    def clean(self):
        cleaned_data = super().clean()
        usar_guardada = cleaned_data.get('usar_tarjeta_guardada', False)
        mes = cleaned_data.get('mes_vencimiento')
        ano = cleaned_data.get('ano_vencimiento')
        numero_tarjeta = cleaned_data.get('numero_tarjeta')
        cvv = cleaned_data.get('cvv')
        nombre_titular = cleaned_data.get('nombre_titular')
        
        if not usar_guardada:
            # Solo validar fecha si no usa tarjeta guardada
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
