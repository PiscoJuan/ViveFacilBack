# Generated by Django 3.1 on 2020-10-09 17:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('api', '0005_auto_20201006_1608'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datos',
            name='tipo',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, to='auth.group'),
        ),
    ]
