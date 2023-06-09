# Generated by Django 3.1 on 2022-04-25 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0175_auto_20220425_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='categoria',
            name='foto2',
            field=models.ImageField(upload_to='categoria2'),
        ),
        migrations.AlterField(
            model_name='pagoefectivo',
            name='valor',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='pagotarjeta',
            name='valor',
            field=models.FloatField(default=0.0),
        ),
    ]
