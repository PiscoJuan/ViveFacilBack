# Generated by Django 3.1.14 on 2023-01-29 13:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0184_auto_20230120_2321'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificacionmasiva',
            name='fecha_creacion',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]