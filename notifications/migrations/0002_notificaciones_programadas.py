from django.db import migrations, models


def backfill(apps, schema_editor):
    """Deja las filas existentes coherentes con la semántica nueva."""
    NotificacionMasiva = apps.get_model('notifications', 'NotificacionMasiva')
    Notificacion = apps.get_model('notifications', 'Notificacion')

    # Las masivas que ya existen SÍ se enviaron: el `crear_notificacion_masiva`
    # viejo disparaba el push en el mismo request de creación. Sin este backfill
    # desaparecen de la lista in-app de las dos apps, porque la visibilidad pasa
    # a exigir `enviada_en` no nulo.
    NotificacionMasiva.objects.filter(enviada_en__isnull=True).update(
        enviada_en=models.F('fecha_creacion'))

    # `frecuencia` era texto libre ('Una vez al día'); con el job nuevo, una fila
    # con hora seteada y estado=1 dispararía sola en la primera corrida. Se
    # normaliza al choice más conservador y se apaga: si alguien la quiere viva,
    # que la reconfigure desde el admin con los campos nuevos.
    Notificacion.objects.all().update(frecuencia='unica', estado=False)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_profesion_pk_int'),
        ('notifications', '0001_initial'),
    ]

    operations = [
        # 1) Alinear el estado de las PK ANTES de crear las M2M. Las columnas ya
        #    son INT(11) en la BD; el modelo heredaba BigAutoField de
        #    notifications/apps.py. Sin esto, las tablas intermedias se crean con
        #    FK BIGINT contra PK INT y MySQL las rechaza (errno 3780), dejando la
        #    migración a medias porque no hay DDL transaccional.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='notificacion',
                    name='id',
                    field=models.AutoField(primary_key=True, serialize=False),
                ),
                migrations.AlterField(
                    model_name='notificacionmasiva',
                    name='id',
                    field=models.AutoField(primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),

        # 2) Columnas nuevas: todas nullable o con default, ALTER seguro.
        migrations.AddField(
            model_name='notificacion',
            name='dirigida_a',
            field=models.CharField(choices=[('solicitante', 'Solo solicitantes'), ('proveedor', 'Solo proveedores'), ('ambas', 'Ambas apps')], default='ambas', max_length=20),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='dias_semana',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='veces_enviada',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='notificacion',
            name='ultimo_envio',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='notificacion',
            name='frecuencia',
            field=models.CharField(choices=[('unica', 'Una sola vez'), ('diaria', 'Todos los días'), ('semanal', 'Días específicos de la semana')], max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='notificacionmasiva',
            name='dirigida_a',
            field=models.CharField(choices=[('solicitante', 'Solo solicitantes'), ('proveedor', 'Solo proveedores'), ('ambas', 'Ambas apps')], default='ambas', max_length=20),
        ),
        migrations.AddField(
            model_name='notificacionmasiva',
            name='programada_para',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notificacionmasiva',
            name='enviada_en',
            field=models.DateTimeField(blank=True, null=True),
        ),

        # 3) M2M: ahora sí generan columnas INT.
        migrations.AddField(
            model_name='notificacion',
            name='profesiones',
            field=models.ManyToManyField(blank=True, db_table='api_notificacion_profesion', related_name='notificaciones_programadas', to='catalog.Profesion'),
        ),
        migrations.AddField(
            model_name='notificacionmasiva',
            name='profesiones',
            field=models.ManyToManyField(blank=True, db_table='api_notificacionmasiva_profesion', related_name='notificaciones_masivas', to='catalog.Profesion'),
        ),

        # 4) Datos.
        migrations.RunPython(backfill, migrations.RunPython.noop),
    ]
