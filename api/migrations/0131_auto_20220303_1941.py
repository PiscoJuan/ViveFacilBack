# Generated by Django 3.1 on 2022-03-04 00:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0130_ciudad'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suggestion',
            name='estado',
            field=models.BooleanField(default=False),
        ),
    ]
