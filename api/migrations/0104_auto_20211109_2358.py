# Generated by Django 3.1 on 2021-11-10 04:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0103_auto_20211109_2356'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proveedor_pendiente',
            name='ano_experiencia',
        ),
        migrations.RemoveField(
            model_name='proveedor_pendiente',
            name='estado',
        ),
    ]
