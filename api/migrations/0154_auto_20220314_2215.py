# Generated by Django 3.1 on 2022-03-15 03:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0153_auto_20220314_1951'),
    ]

    operations = [
        migrations.RenameField(
            model_name='planproveedor',
            old_name='plan',
            new_name='planProveedor',
        ),
    ]
