# Generated by Django 3.1 on 2022-03-13 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0143_auto_20220313_1012'),
    ]

    operations = [
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='copiaLicencia',
            field=models.FileField(null=True, upload_to='documents'),
        ),
    ]
