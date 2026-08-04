import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_cargo_tipo'),
        # 0005 fijó Datos.id a AutoField (state-only); la FK de abajo lo necesita.
        ('accounts', '0007_datos_fecha_modificacion'),
    ]

    operations = [
        # api_insignia.id ya es INT en la BD; solo alineamos el estado de Django
        # (el app_config global usa BigAutoField). Sin operación de BD: la FK
        # nueva saldría bigint y MySQL la rechaza (errno 3780), y como no hay
        # DDL transaccional la tabla quedaría creada a medias.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='insignia',
                    name='id',
                    field=models.AutoField(primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
        migrations.CreateModel(
            name='InsigniaObtenida',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('fecha_obtencion', models.DateTimeField(default=django.utils.timezone.now)),
                ('insignia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content.insignia')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              related_name='insignias_obtenidas', to='accounts.datos')),
            ],
            options={
                'db_table': 'api_insignia_obtenida',
                'unique_together': {('usuario', 'insignia')},
            },
        ),
        # null=True: las filas viejas se quedan sin fecha, no se inventa una.
        migrations.AddField(
            model_name='clientexmedalla',
            name='fecha_obtencion',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
    ]
