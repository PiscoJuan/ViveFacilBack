import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0004_categoria_pk_int'),
        ('promotions', '0004_cupon_categoria_fk'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cuponcategoria',
            name='categoria',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='catalog.categoria',
            ),
        ),
    ]
