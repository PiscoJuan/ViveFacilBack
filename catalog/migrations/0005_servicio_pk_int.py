from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_categoria_pk_int'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name='servicio',
                    name='id',
                    field=models.AutoField(primary_key=True, serialize=False),
                ),
            ],
            database_operations=[],
        ),
    ]
