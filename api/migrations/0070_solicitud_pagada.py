# Generated by Django 3.1 on 2021-01-29 13:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0069_pagoefectivo_pagotarjeta'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitud',
            name='pagada',
            field=models.BooleanField(default=False),
        ),
    ]
