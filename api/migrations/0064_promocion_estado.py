# Generated by Django 3.1 on 2021-01-28 20:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0063_promocion'),
    ]

    operations = [
        migrations.AddField(
            model_name='promocion',
            name='estado',
            field=models.BooleanField(default=True),
        ),
    ]
