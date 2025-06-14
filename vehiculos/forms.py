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