# Generated by Django 3.1 on 2022-04-06 16:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0159_notificacionmasiva'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='profesion_proveedor',
            name='proveedor',
        ),
        migrations.AddField(
            model_name='proveedor',
            name='profesiones',
            field=models.ManyToManyField(to='api.Profesion_Proveedor'),
        ),
    ]