# Generated by Django 3.1 on 2022-03-12 23:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0141_auto_20220312_1641'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='proveedor',
            name='id_plan_proveedor',
        ),
        migrations.AddField(
            model_name='planproveedor',
            name='proveedor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.proveedor'),
        ),
    ]
