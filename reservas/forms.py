from django import forms
from .models import Reserva
import datetime

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
