# Generated by Django 3.1 on 2022-03-15 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0154_auto_20220314_2215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='proveedor_pendiente',
            name='copiaCedula',
            field=models.FileField(null=True, upload_to='pendientes-copias'),
        ),
        migrations.AlterField(
            model_name='proveedor_pendiente',
            name='copiaLicencia',
            field=models.FileField(null=True, upload_to='pendientes-copias'),
        ),
    ]