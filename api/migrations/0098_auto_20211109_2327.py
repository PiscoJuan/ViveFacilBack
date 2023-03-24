# Generated by Django 3.1 on 2021-11-10 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0097_auto_20211109_2314'),
    ]

    operations = [
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='ano_experiencia',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='banco',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='cedula',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='email',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='estado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='numero_cuenta',
            field=models.CharField(default='', max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='profesion',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='telefono',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='tipo_cuenta',
            field=models.CharField(default='', max_length=50, null=True),
        ),
    ]