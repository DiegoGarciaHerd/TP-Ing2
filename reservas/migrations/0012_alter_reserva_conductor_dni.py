# Generated by Django 5.2 on 2025-07-11 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservas', '0011_alter_reserva_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reserva',
            name='conductor_dni',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
