# Generated by Django 3.1 on 2020-10-03 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_auto_20201003_0107'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datos',
            name='ciudad',
            field=models.CharField(default='No especificado', max_length=255),
        ),
    ]