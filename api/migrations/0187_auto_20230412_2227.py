# Generated by Django 3.1.14 on 2023-04-13 03:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0186_proveedor_pendiente_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicio',
            name='foto',
            field=models.ImageField(null=True, upload_to='servicio'),
        ),
        migrations.AlterField(
            model_name='proveedor_pendiente',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='foto_proveedor'),
        ),
    ]
