# Generated by Django 3.1 on 2020-12-30 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0058_auto_20201208_2147'),
    ]

    operations = [
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='documento',
            field=models.FileField(null=True, upload_to='documents'),
        ),
    ]
