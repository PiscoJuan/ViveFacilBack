# Generated by Django 3.1 on 2022-04-22 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0172_auto_20220422_1543'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagoefectivo',
            name='proveedor',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='pagoefectivo',
            name='servicio',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='pagoefectivo',
            name='usuario',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AddField(
            model_name='pagotarjeta',
            name='usuario',
            field=models.CharField(default='', max_length=255),
        ),
    ]
