# Generated by Django 3.1 on 2020-11-22 23:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0036_solicitud_adjudicar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='solicitud',
            name='proveedor',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]