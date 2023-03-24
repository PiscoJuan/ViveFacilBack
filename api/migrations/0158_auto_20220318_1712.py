# Generated by Django 3.1 on 2022-03-18 22:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0157_auto_20220317_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacion',
            name='imagen',
            field=models.ImageField(blank=True, null=True, upload_to='notificaciones'),
        ),
        migrations.AlterField(
            model_name='proveedor',
            name='copiaCedula',
            field=models.FileField(null=True, upload_to='documentos-Proveedor'),
        ),
        migrations.AlterField(
            model_name='proveedor',
            name='copiaLicencia',
            field=models.FileField(null=True, upload_to='documentos-Proveedor'),
        ),
    ]