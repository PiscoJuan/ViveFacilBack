# Generated by Django 3.1 on 2020-10-27 21:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_envio_interesados_oferta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='envio_interesados',
            name='oferta',
            field=models.DecimalField(blank=True, decimal_places=10, max_digits=10, null=True),
        ),
    ]
