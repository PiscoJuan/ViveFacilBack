# Generated by Django 3.1 on 2022-02-25 22:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0124_auto_20220225_1705'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plan',
            name='imagen',
            field=models.ImageField(null=True, upload_to='planes'),
        ),
    ]