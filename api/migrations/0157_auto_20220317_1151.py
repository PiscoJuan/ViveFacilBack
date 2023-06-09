# Generated by Django 3.1 on 2022-03-17 16:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0156_proveedor_pendiente_descripcion'),
    ]

    operations = [
        migrations.AddField(
            model_name='proveedor',
            name='copiaCedula',
            field=models.FileField(null=True, upload_to='documnts'),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='copiaLicencia',
            field=models.FileField(null=True, upload_to='documents'),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='direccion',
            field=models.CharField(default='', max_length=300),
        ),
        migrations.AddField(
            model_name='proveedor',
            name='licencia',
            field=models.CharField(default='', max_length=55),
        ),
    ]
