from django.db import migrations

def update_vehicle_types(apps, schema_editor):
    Vehiculo = apps.get_model('vehiculos', 'Vehiculo')
    
    # Mapeo de tipos antiguos a nuevos
    type_mapping = {
        'SEDAN': 'AUTOMOVIL',
        'COMPACTO': 'AUTOMOVIL',
        'DEPORTIVO': 'AUTOMOVIL',
        'SUV': '4X4',
        'PICKUP': 'CAMIONETA',
        'VAN': 'CAMIONETA'
    }
    
    # Actualizar todos los vehículos
    for vehiculo in Vehiculo.objects.all():
        if vehiculo.tipo in type_mapping:
            vehiculo.tipo = type_mapping[vehiculo.tipo]
            vehiculo.save()

class Migration(migrations.Migration):
    dependencies = [
        ('vehiculos', '0004_vehiculo_capacidad_vehiculo_tipo'),
    ]

    operations = [
        migrations.RunPython(update_vehicle_types),
    ] 