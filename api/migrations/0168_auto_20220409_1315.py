# Generated by Django 3.1 on 2022-04-09 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0167_auto_20220409_1126'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cargo',
            name='porcentaje',
            field=models.FloatField(default=0.0),
        ),
    ]