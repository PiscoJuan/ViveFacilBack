# Generated by Django 3.1 on 2021-11-10 05:02

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0105_auto_20211109_2359'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proveedor_pendiente',
            name='banco',
        ),
        migrations.RemoveField(
            model_name='proveedor_pendiente',
            name='numero_cuenta',
        ),
        migrations.RemoveField(
            model_name='proveedor_pendiente',
            name='tipo_cuenta',
        ),
    ]