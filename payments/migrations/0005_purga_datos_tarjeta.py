"""
Purga los datos sensibles que quedaron en api_tarjeta: cvv y numero (PAN).
Las tarjetas reales viven en Paymentez; estos campos ya no se usan ni se
exponen. No se pueden poner a NULL (no-nullables), así que se neutralizan.
"""
from django.db import migrations


def purgar(apps, schema_editor):
    Tarjeta = apps.get_model("payments", "Tarjeta")
    Tarjeta.objects.exclude(cvv="***").update(cvv="***")
    Tarjeta.objects.exclude(numero=0).update(numero=0)


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0004_auto_20260707_1831"),
    ]

    operations = [
        # Solo purga de datos; irreversible (no se restauran datos sensibles).
        migrations.RunPython(purgar, migrations.RunPython.noop),
    ]
