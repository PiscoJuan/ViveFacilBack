# Generated by Django 3.1 on 2022-03-14 23:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0150_pendientedocuments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pendientedocuments',
            name='pendiente',
        ),
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='documentsPendientes',
            field=models.ManyToManyField(to='api.PendienteDocuments'),
        ),
    ]
