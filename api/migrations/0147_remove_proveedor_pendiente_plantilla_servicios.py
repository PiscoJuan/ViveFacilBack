# Generated by Django 3.1 on 2022-03-13 21:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0146_proveedor_pendiente_plantilla_servicios'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proveedor_pendiente',
            name='plantilla_servicios',
        ),
    ]
