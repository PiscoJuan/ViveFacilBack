# Generated by Django 3.1 on 2021-05-24 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0086_auto_20210524_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitud',
            name='fecha_expiracion',
            field=models.DateField(),
        ),
    ]
