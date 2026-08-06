from django.db import migrations, models


class Migration(migrations.Migration):
    """Alinea el estado de Django con la BD para `api_categoria.id`.

    La columna ya es INT(11); lo que estaba mal era el modelo, que heredaba
    BigAutoField de catalog/apps.py. Mientras nadie apuntara una FK nueva hacia
    Categoria daba igual, pero promotions.Cupon.categoria sí lo hace y MySQL
    rechaza una FK BIGINT contra un PK INT (errno 3780).

    Sin operaciones de BD: un MODIFY sobre un PK referenciado por
    api_servicio, api_cuponcategoria, etc. es innecesario y riesgoso. Mismo
    patrón que catalog/migrations/0003_profesion_pk_int.py.
    """

    dependencies = [
        ('catalog', '0003_profesion_pk_int'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='categoria',
                    name='id',
                    field=models.AutoField(primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
