# Generated by Django 3.1 on 2020-10-12 15:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_auto_20201010_1219'),
    ]

    operations = [
        migrations.AddField(
            model_name='servicio',
            name='foto',
            field=models.ImageField(null=True, upload_to='servicio'),
        ),
        migrations.AddField(
            model_name='ubicacion',
            name='direccion',
            field=models.CharField(max_length=300, null=True),
        ),
    ]