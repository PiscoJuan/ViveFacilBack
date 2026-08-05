from django.db import migrations, models


class Migration(migrations.Migration):
    """Alinea el estado de Django con la BD para `api_profesion.id`.

    La columna ya es INT(11); lo que estaba mal era el modelo, que heredaba
    BigAutoField de catalog/apps.py. Mientras nadie apuntara una FK nueva hacia
    Profesion daba igual, pero la M2M de notifications sí lo hace y MySQL
    rechaza una FK BIGINT contra un PK INT (errno 3780).

    Sin operaciones de BD: un MODIFY sobre un PK referenciado por
    api_profesion_servicio y api_profesion_proveedor es innecesario y riesgoso.
    Mismo patrón que accounts/0005 para api_datos.
    """

    dependencies = [
        ('catalog', '0002_auto_20260707_1831'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='profesion',
                    name='id',
                    field=models.AutoField(primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
