import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class MinimumLengthValidator:
    """
    Valida que la contraseña tenga al menos 5 caracteres.
    """
    def __init__(self, min_length=5):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("Esta contraseña es demasiado corta. Debe contener al menos %(min_length)d caracteres."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _(
            "Tu contraseña debe contener al menos %(min_length)d caracteres."
            % {'min_length': self.min_length}
        )

class AlphabetValidator:
    """
    Valida que la contraseña contenga al menos una letra del abecedario occidental.
    """
    def validate(self, password, user=None):
        if not re.search('[a-zA-Z]', password):
            raise ValidationError(
                _("Tu contraseña debe contener al menos una letra."),
                code='password_no_letter',
            )

    def get_help_text(self):
        return _("Tu contraseña debe contener al menos una letra.")

class NumericValidator:
    """
    Valida que la contraseña contenga al menos un dígito.
    """
    def validate(self, password, user=None):
        if not re.search('[0-9]', password):
            raise ValidationError(
                _("Tu contraseña debe contener al menos un dígito."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _("Tu contraseña debe contener al menos un dígito (0-9).")


def validar_edad(edad):
    """Valida que la edad sea mayor o igual a 18 años"""
    if edad < 18:
        raise ValidationError('Debe ser mayor de 18 años para registrarse.')


def validar_dni(dni):
    """Valida el formato del DNI argentino"""
    # Eliminar espacios y puntos
    dni_limpio = re.sub(r'[\s\.]', '', str(dni))
    
    # Verificar que solo contenga dígitos
    if not dni_limpio.isdigit():
        raise ValidationError('El DNI debe contener solo números.')
    
    # Verificar longitud (7-8 dígitos para DNI argentino)
    if len(dni_limpio) < 7 or len(dni_limpio) > 8:
        raise ValidationError('El DNI debe tener entre 7 y 8 dígitos.')
    
    return dni_limpio 