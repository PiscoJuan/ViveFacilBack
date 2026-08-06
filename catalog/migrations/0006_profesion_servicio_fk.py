import django.db.models.deletion
from django.db import migrations, models


# Profesion.servicio pasa de ManyToMany (usado siempre como 1:1, .clear()+.add()
# de un solo servicio) a ForeignKey real. Antes del FK, el emparejamiento
# efectivo entre Profesion y Servicio para buscar proveedores se resolvía en
# tiempo de consulta comparando nombres (ver catalog/services.py) — la
# migración de datos usa el mismo criterio de respaldo (nombre idéntico)
# cuando no había fila en la M2M, para no perder ningún emparejamiento que
# hoy funciona en producción.
def poblar_servicio_fk(apps, schema_editor):
    Profesion = apps.get_model('catalog', 'Profesion')
    Servicio = apps.get_model('catalog', 'Servicio')
    for profesion in Profesion.objects.all():
        servicio = profesion.servicio.first()
        if servicio is None:
            servicio = Servicio.objects.filter(nombre=profesion.nombre).first()
        if servicio is not None:
            profesion.servicio_fk_id = servicio.id
            profesion.save(update_fields=['servicio_fk'])


def revertir_servicio_fk(apps, schema_editor):
    Profesion = apps.get_model('catalog', 'Profesion')
    for profesion in Profesion.objects.exclude(servicio_fk__isnull=True):
        profesion.servicio.add(profesion.servicio_fk_id)


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_servicio_pk_int'),
    ]

    operations = [
        migrations.AddField(
            model_name='profesion',
            name='servicio_fk',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                related_name='profesiones', to='catalog.servicio',
            ),
        ),
        migrations.RunPython(poblar_servicio_fk, revertir_servicio_fk),
        migrations.RemoveField(
            model_name='profesion',
            name='servicio',
        ),
        migrations.RenameField(
            model_name='profesion',
            old_name='servicio_fk',
            new_name='servicio',
        ),
    ]
