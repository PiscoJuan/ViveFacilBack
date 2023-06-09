# Generated by Django 3.1 on 2021-12-13 14:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0113_delete_subcategoria'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ciudad_Disponible',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Cupon',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(max_length=25, null=True, unique=True)),
                ('titulo', models.CharField(max_length=255, null=True)),
                ('descripcion', models.CharField(max_length=255, null=True)),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, null=True)),
                ('fecha_expiracion', models.DateTimeField()),
                ('porcentaje', models.IntegerField()),
                ('puntos', models.IntegerField()),
                ('estado', models.BooleanField(default=True)),
                ('foto', models.ImageField(blank=True, null=True, upload_to='promociones')),
                ('tipo_categoria', models.CharField(max_length=25, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CuponCategoria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, null=True)),
                ('estado', models.BooleanField(default=True)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.categoria')),
                ('cupon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.cupon')),
            ],
        ),
    ]
