# Generated by Django 3.1 on 2021-04-22 01:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0082_auto_20210412_1955'),
    ]

    operations = [
        migrations.AddField(
            model_name='solicitud',
            name='rating',
            field=models.FloatField(default=4.0),
        ),
    ]
