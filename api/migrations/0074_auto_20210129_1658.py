# Generated by Django 3.1 on 2021-01-29 21:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0073_remove_pagoefectivo_impuesto'),
    ]

    operations = [
        migrations.AddField(
            model_name='pagotarjeta',
            name='carrier_code',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='pagotarjeta',
            name='carrier_id',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
