from django import forms
from .models import Reserva
import datetime
import re
from django.db import models
from usuarios.models import Usuario

class ReservaForm(forms.ModelForm):
    # Ya no declaramos 'cliente_seleccionado' directamente aquí.
    # Lo agregaremos dinámicamente en __init__

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

    # Campos para extras
    silla_para_ninos = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Silla para niños"
    )
    telepass = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="TelePase habilitado"
    )
    seguro_por_danos = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Seguro por daños"
    )
    conductor_adicional = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Conductor adicional"
    )
    conductor_adicional_nombre = forms.CharField(
        label="Nombre del Conductor Adicional",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    conductor_adicional_apellido = forms.CharField(
        label="Apellido del Conductor Adicional",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    conductor_adicional_dni = forms.CharField(
        label="DNI del Conductor Adicional",
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Reserva
        # IMPORTANTE: No incluyas 'cliente_seleccionado' aquí en 'fields'.
        # Lo manejaremos dinámicamente.
        fields = [
            'fecha_recogida', 'fecha_devolucion',
            'conductor_nombre', 'conductor_apellido', 'conductor_dni',
            'silla_para_ninos', 'telepass', 'seguro_por_danos', 'conductor_adicional',
            'conductor_adicional_nombre', 'conductor_adicional_apellido', 'conductor_adicional_dni'
        ]
        labels = {
            'fecha_recogida': 'Fecha de Recogida',
            'fecha_devolucion': 'Fecha de Devolución',
            'conductor_nombre': 'Nombre del Conductor',
            'conductor_apellido': 'Apellido del Conductor',
            'conductor_dni': 'DNI del Conductor',
            'silla_para_ninos': 'Silla para niños',
            'telepass': 'TelePase habilitado',
            'seguro_por_danos': 'Seguro por daños',
            'conductor_adicional': 'Conductor adicional',
            'conductor_adicional_nombre': 'Nombre del Conductor Adicional',
            'conductor_adicional_apellido': 'Apellido del Conductor Adicional',
            'conductor_adicional_dni': 'DNI del Conductor Adicional',
        }
        help_texts = {
            'fecha_recogida': 'Formato: AAAA-MM-DD',
            'fecha_devolucion': 'Formato: AAAA-MM-DD',
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha_recogida = cleaned_data.get('fecha_recogida')
        fecha_devolucion = cleaned_data.get('fecha_devolucion')
        conductor_dni = cleaned_data.get('conductor_dni')
        conductor_adicional = cleaned_data.get('conductor_adicional')
        conductor_adicional_dni = cleaned_data.get('conductor_adicional_dni')
        conductor_adicional_nombre = cleaned_data.get('conductor_adicional_nombre')
        conductor_adicional_apellido = cleaned_data.get('conductor_adicional_apellido')
        
        # Validación adicional para contexto de empleados
        if self.is_employee_context:
            cliente_seleccionado = cleaned_data.get('cliente_seleccionado')
            if cliente_seleccionado:
                # Verificar que el cliente seleccionado no sea un empleado
                if cliente_seleccionado.rol != 'CLIENTE':
                    self.add_error('cliente_seleccionado', "Solo se pueden crear reservas para clientes, no para empleados o administradores.")
                
                # Verificar que el usuario no tenga perfil de empleado
                if hasattr(cliente_seleccionado, 'empleado_profile'):
                    self.add_error('cliente_seleccionado', "No se pueden crear reservas para usuarios que tienen perfil de empleado.")

        
        if fecha_recogida and fecha_devolucion:
            if fecha_devolucion < fecha_recogida:
                self.add_error('fecha_devolucion', "La fecha de devolución no puede ser anterior a la fecha de recogida.")


        #
        if conductor_dni and fecha_recogida and fecha_devolucion:
            
            cliente_seleccionado = cleaned_data.get('cliente_seleccionado')  # ya lo habías definido antes

            overlapping_main_driver_reservations = Reserva.objects.filter(
                conductor_dni=conductor_dni,
                fecha_recogida__lt=fecha_devolucion,
                fecha_devolucion__gt=fecha_recogida,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'RETIRADO']
            ).exclude(cliente=cliente_seleccionado)

            if cliente_seleccionado:
                overlapping_main_driver_reservations = overlapping_main_driver_reservations.exclude(cliente=cliente_seleccionado)

            if self.instance and self.instance.pk:
                overlapping_main_driver_reservations = overlapping_main_driver_reservations.exclude(pk=self.instance.pk)

            if overlapping_main_driver_reservations.exists():
                self.add_error('conductor_dni', "Este DNI ya está asignado a otra reserva activa como conductor principal en las fechas seleccionadas.")


            if overlapping_main_driver_reservations.exists():
                self.add_error('conductor_dni', "Este DNI ya está asignado a otra reserva activa como conductor principal en las fechas seleccionadas.")
            
           
            overlapping_additional_driver_reservations = Reserva.objects.filter(
                conductor_adicional_dni=conductor_dni,
                fecha_recogida__lt=fecha_devolucion,
                fecha_devolucion__gt=fecha_recogida,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'RETIRADO']
            )
            if self.instance and self.instance.pk: # Exclude current reservation if updating
                overlapping_additional_driver_reservations = overlapping_additional_driver_reservations.exclude(pk=self.instance.pk)

            if overlapping_additional_driver_reservations.exists():
                self.add_error('conductor_dni', "Este DNI ya está asignado a otra reserva activa como conductor adicional en las fechas seleccionadas.")


       
        if conductor_adicional:
            if not conductor_adicional_dni or not conductor_adicional_nombre or not conductor_adicional_apellido:
                self.add_error('conductor_adicional', "Debe completar todos los datos del conductor adicional si marca esta opción.")

            if conductor_adicional_dni == conductor_dni:
                self.add_error('conductor_adicional_dni', "El DNI del conductor adicional no puede ser igual al del conductor principal.")

            if conductor_adicional_dni and fecha_recogida and fecha_devolucion:
                
                overlapping_reservations = Reserva.objects.filter(
                    (models.Q(conductor_dni=conductor_adicional_dni) | models.Q(conductor_adicional_dni=conductor_adicional_dni)),
                    fecha_recogida__lt=fecha_devolucion,
                    fecha_devolucion__gt=fecha_recogida,
                    estado__in=['PENDIENTE', 'CONFIRMADA', 'RETIRADO']
                )
                if self.instance and self.instance.pk: # Exclude current reservation if updating
                    overlapping_reservations = overlapping_reservations.exclude(pk=self.instance.pk)

                if overlapping_reservations.exists():
                    self.add_error('conductor_adicional_dni', "El conductor adicional ya tiene una reserva activa (como principal o adicional) en las fechas seleccionadas.")
        else:
          
            cleaned_data['conductor_adicional_dni'] = ''
            cleaned_data['conductor_adicional_nombre'] = ''
            cleaned_data['conductor_adicional_apellido'] = ''

        return cleaned_data

    def __init__(self, *args, **kwargs):
       
        self.is_employee_context = kwargs.pop('is_employee_context', False)
        self.vehiculo = kwargs.pop('vehiculo', None)
        super().__init__(*args, **kwargs)
        
       
        today_iso = datetime.date.today().isoformat()
        self.fields['fecha_recogida'].widget.attrs['min'] = today_iso
        self.fields['fecha_devolucion'].widget.attrs['min'] = today_iso

        # --- Lógica Condicional para 'cliente_seleccionado' ---
        if self.is_employee_context:
            # If an employee is creating the reservation, add the field and make it required
            # Filtrar SOLO clientes, excluyendo explícitamente empleados y administradores
            
            # DEBUG: Verificar qué usuarios existen y sus roles
            print("=== DEBUG USUARIOS EN SISTEMA ===")
            todos_usuarios = Usuario.objects.all()
            for usuario in todos_usuarios:
                print(f"Usuario: {usuario.get_full_name()} | Email: {usuario.email} | Rol: {usuario.rol} | Activo: {usuario.is_active}")
            
            # DEBUG: Verificar el queryset filtrado
            # Excluir usuarios que tengan perfil de empleado, incluso si su rol es 'CLIENTE'
            queryset_filtrado = Usuario.objects.filter(
                rol='CLIENTE',
                is_active=True
            ).exclude(
                rol__in=['EMPLEADO', 'ADMIN']
            ).exclude(
                empleado_profile__isnull=False  # Excluir usuarios que tengan perfil de empleado
            ).order_by('last_name', 'first_name')
            
            print(f"\n=== DEBUG QUERYSET FILTRADO ===")
            print(f"Total usuarios en queryset filtrado: {queryset_filtrado.count()}")
            for usuario in queryset_filtrado:
                print(f"Usuario en queryset: {usuario.get_full_name()} | Email: {usuario.email} | Rol: {usuario.rol}")
            
            self.fields['cliente_seleccionado'] = forms.ModelChoiceField(
                queryset=queryset_filtrado,
                label="Cliente para la Reserva",
                empty_label="--- Seleccionar Cliente ---",
                required=True, # Obligatorio para empleados
                widget=forms.Select(attrs={'class': 'form-control'})
            )
            # Make sure it's the first field in the form
            # You might need to adjust the order if other fields are added dynamically
            field_order = ['cliente_seleccionado'] + list(self.fields.keys())
            self.order_fields(field_order)
        else:
            # If a client is creating the reservation, remove the field
            if 'cliente_seleccionado' in self.fields: # Check if it somehow was added
                del self.fields['cliente_seleccionado']
            # Also ensure it's not expected in the Meta.fields (already removed above)

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
        numero_tarjeta = self.cleaned_data.get('numero_tarjeta', '')
        
        if not cvv:
            raise forms.ValidationError("El CVV es requerido.")
            
        if not cvv.isdigit():
            raise forms.ValidationError("El CVV debe contener solo dígitos.")
            
        if len(cvv) < 3 or len(cvv) > 4:
            raise forms.ValidationError("El CVV debe tener 3 o 4 dígitos.")
            
        # Limpiar número de tarjeta (eliminar espacios y guiones)
        numero_limpio = re.sub(r'[\s-]', '', numero_tarjeta)
        
        # Validar CVV específico para cada tarjeta
        if numero_limpio == '4517660196851645' and cvv != '789':
            raise forms.ValidationError("CVV incorrecto para esta tarjeta.")
        elif numero_limpio == '5258556802017961' and cvv != '345':
            raise forms.ValidationError("CVV incorrecto para esta tarjeta.")
            
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
                
                # Tarjetas permitidas con los CVV específicos
                tarjetas_permitidas = [
                    {
                        'numero': '4517660196851645',
                        'mes': '8',
                        'ano': '2030',
                        'cvv': '789',  # CVV actualizado
                        'nombre': 'CONRADO FEDERICO ESCOBARES'
                    },
                    {
                        'numero': '5258556802017961',
                        'mes': '8',
                        'ano': '2029',
                        'cvv': '345',  # CVV actualizado
                        'nombre': 'ESCOBARES CONRADO F'
                    }
                ]
                
                # Verificar si la tarjeta coincide con alguna permitida
                tarjeta_valida = False
                
                for tarjeta in tarjetas_permitidas:
                    if (numero_limpio == tarjeta['numero'] and
                        str(mes) == tarjeta['mes'] and
                        str(ano) == tarjeta['ano'] and
                        cvv == tarjeta['cvv'] and
                        nombre_titular.upper() == tarjeta['nombre']):
                        tarjeta_valida = True
                        break
                
                if not tarjeta_valida:
                    raise forms.ValidationError("Los datos de la tarjeta no coinciden con una tarjeta autorizada o el CVV es incorrecto.")
        
        return cleaned_data

class ExtrasReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = [
            'silla_para_ninos',
            'telepass',
            'seguro_por_danos',
            'conductor_adicional',
            'conductor_adicional_nombre',
            'conductor_adicional_apellido',
            'conductor_adicional_dni',
        ]
        widgets = {
            'silla_para_ninos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'telepass': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'seguro_por_danos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'conductor_adicional': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'conductor_adicional_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'conductor_adicional_apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'conductor_adicional_dni': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        conductor_adicional = cleaned_data.get('conductor_adicional')
        conductor_adicional_dni = cleaned_data.get('conductor_adicional_dni')
        conductor_adicional_nombre = cleaned_data.get('conductor_adicional_nombre')
        conductor_adicional_apellido = cleaned_data.get('conductor_adicional_apellido')

        if conductor_adicional:
            if not conductor_adicional_dni or not conductor_adicional_nombre or not conductor_adicional_apellido:
                raise forms.ValidationError("Debe completar todos los datos del conductor adicional.")

            # Verificar que el DNI del conductor adicional no sea igual al del conductor principal
            if self.instance.conductor_dni == conductor_adicional_dni:
                raise forms.ValidationError("El DNI del conductor adicional no puede ser igual al del conductor principal.")

            # Verificar que el conductor adicional no tenga otra reserva
            if Reserva.objects.filter(conductor_dni=conductor_adicional_dni).exclude(id=self.instance.id).exists() or \
               Reserva.objects.filter(conductor_adicional_dni=conductor_adicional_dni).exclude(id=self.instance.id).exists():
                raise forms.ValidationError("El conductor adicional ya tiene una reserva asignada.")

        return cleaned_data
