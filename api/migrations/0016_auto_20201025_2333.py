# Generated by Django 3.1 on 2020-10-26 04:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_auto_20201025_2320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitud',
            name='proveedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.proveedor'),
        ),
    ]
