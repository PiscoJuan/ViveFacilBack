# Generated by Django 3.1 on 2021-01-30 01:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0075_auto_20210129_1952'),
    ]

    operations = [
        migrations.AlterField(
            model_name='codigos',
            name='user_datos',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.datos'),
        ),
    ]