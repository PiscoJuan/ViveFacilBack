# Generated by Django 3.1 on 2020-12-09 02:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0052_auto_20201129_0430'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notificaciones',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, null=True)),
                ('descripcion', models.CharField(max_length=255, null=True)),
                ('tipo', models.CharField(max_length=50, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, null=True)),
                ('user_datos', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.datos')),
            ],
        ),
    ]
