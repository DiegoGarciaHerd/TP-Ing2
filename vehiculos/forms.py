from django import forms
from .models import Vehiculo

class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = '__all__'
        widgets = {
            'politica_reembolso': forms.RadioSelect(choices=[
                (0, 'No reembolsable (0%)'),
                (20, 'Reembolso parcial (20%)'),
                (100, 'Reembolso total (100%)'),
            ]),
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'fecha_adquisicion': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'politica_reembolso': 'Seleccione la política aplicable para este vehículo',
        }

class VehiculoEmpleadoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['precio_por_dia', 'foto_base64', 'politica_de_reembolso', 'kilometraje', 'estado']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limitar las opciones de estado solo a Disponible y En mantenimiento
        self.fields['estado'].choices = [
            ('DISPONIBLE', 'Disponible'),
            ('EN_MANTENIMIENTO', 'En mantenimiento'),
        ]
        
        # Configurar widgets para mejor experiencia de usuario
        self.fields['precio_por_dia'].widget = forms.NumberInput(attrs={'step': '0.01'})
        self.fields['kilometraje'].widget = forms.NumberInput(attrs={'min': '0'})