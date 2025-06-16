from django import forms
from empleados.models import Empleado

class ModificarEmpleadoForm(forms.ModelForm):
    dni = forms.ModelChoiceField(
        # --- CAMBIO AQUÍ ---
        queryset=Empleado.objects.filter(activo=True).order_by('apellido', 'nombre'), # Filtrar por activo=True
        # -------------------
        empty_label="Seleccione un empleado",
        to_field_name="dni",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Seleccionar Empleado"
    )
    
    nombre = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    apellido = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    direccion = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    telefono = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )

    class Meta:
        model = Empleado
        fields = ['dni', 'nombre', 'apellido', 'email', 'direccion', 'telefono']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar el queryset para mostrar nombre y apellido en el select
        self.fields['dni'].label_from_instance = lambda obj: f"{obj.nombre} {obj.apellido} ({obj.dni})"