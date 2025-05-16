from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    capacidad_personas = models.IntegerField()
    precio_diario = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.nombre

class Vehiculo(models.Model):
    ESTADOS = (
        ('DISPONIBLE', 'Disponible'),
        ('RESERVADO', 'Reservado'),
        ('MANTENIMIENTO', 'En mantenimiento'),
        ('ALQUILADO', 'Alquilado'),
    )
    
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    año = models.IntegerField()
    patente = models.CharField(max_length=10, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='DISPONIBLE')
    sucursal = models.ForeignKey('empleados.Sucursal', on_delete=models.PROTECT)
    imagen = models.ImageField(upload_to='vehiculos/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.marca} {self.modelo} ({self.patente})"