# Generated by Django 3.1 on 2021-08-28 00:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0090_auto_20210827_1857'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datos',
            name='codigo_invitacion',
            field=models.CharField(default='', max_length=20),
        ),
    ]