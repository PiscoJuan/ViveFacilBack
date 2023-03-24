# Generated by Django 3.1 on 2021-01-28 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0062_solicitud_termino'),
    ]

    operations = [
        migrations.CreateModel(
            name='Promocion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=255, null=True)),
                ('descripcion', models.CharField(max_length=255, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, null=True)),
                ('fecha_expiracion', models.DateTimeField()),
                ('porcentaje', models.IntegerField()),
            ],
        ),
    ]