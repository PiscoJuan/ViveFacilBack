# Generated by Django 3.1 on 2020-10-10 17:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('api', '0006_auto_20201009_1207'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datos',
            name='tipo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='auth.group'),
        ),
    ]
