# Generated by Django 3.1 on 2020-11-24 22:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0041_auto_20201124_1724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitud',
            name='proveedor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='api.proveedor'),
        ),
    ]