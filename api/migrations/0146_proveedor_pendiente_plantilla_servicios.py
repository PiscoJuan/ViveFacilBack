# Generated by Django 3.1 on 2022-03-13 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0145_auto_20220313_1113'),
    ]

    operations = [
        migrations.AddField(
            model_name='proveedor_pendiente',
            name='plantilla_servicios',
            field=models.FileField(null=True, upload_to='documents'),
        ),
    ]
