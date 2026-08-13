import logging

from django.conf import settings
from django.db import transaction
from django.db.models import FileField, ImageField
from django.db.models.fields.files import FieldFile, ImageFieldFile

from core.archivos import ruta_relativa

logger = logging.getLogger(__name__)


def borrar_del_storage(storage, nombre):
    """Un archivo que no se pudo borrar es basura en disco, no un error de
    negocio: corre en un hook de on_commit, o sea después del COMMIT, así que
    dejar escapar la excepción rompe el proceso con los datos ya guardados."""
    try:
        storage.delete(ruta_relativa(nombre))
    except Exception:
        logger.warning("No se pudo borrar el archivo %s", nombre, exc_info=True)


def borrar_archivos_al_eliminar(sender, instance, **kwargs):
    """Receptor de post_delete: borra del storage los archivos de la fila que
    se elimina. Se conecta sin `sender` (core/apps.py) para cubrir todos los
    modelos; los que no tienen FileField salen en el primer for.
    """
    for campo in instance._meta.concrete_fields:
        if not isinstance(campo, FileField):
            continue
        nombre = getattr(instance, campo.attname).name
        if nombre:
            transaction.on_commit(
                lambda storage=campo.storage, nombre=nombre: borrar_del_storage(storage, nombre))


class BorraAnteriorMixin:
    """Django nunca borra del disco el archivo que se reemplaza (solo cambia la
    ruta en la columna). Lo hacemos aquí, en el campo, para cubrir de una vez
    los ~20 FileField/ImageField del proyecto sin tocar cada modelo.

    ponytail: el borrado va en on_commit, así un rollback no deja la fila
    apuntando a un archivo ya borrado.
    """

    def pre_save(self, model_instance, add):
        archivo = super().pre_save(model_instance, add)
        if not add and model_instance.pk:
            anterior = (
                model_instance.__class__._base_manager
                .filter(pk=model_instance.pk)
                .values_list(self.attname, flat=True)
                .first()
            )
            if anterior and ruta_relativa(anterior) != ruta_relativa(archivo.name):
                transaction.on_commit(lambda: borrar_del_storage(self.storage, anterior))
        return archivo


class URLCompletaFieldFile(FieldFile):
    @property
    def url(self):
        return settings.URL_BACKEND_HOST.rstrip('/') + super().url


class URLCompletaImageFieldFile(ImageFieldFile):
    @property
    def url(self):
        return settings.URL_BACKEND_HOST.rstrip('/') + super().url


class URLCompletaFileField(BorraAnteriorMixin, FileField):
    attr_class = URLCompletaFieldFile

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'django.db.models.FileField', args, kwargs


class URLCompletaImageField(BorraAnteriorMixin, ImageField):
    attr_class = URLCompletaImageFieldFile

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        return name, 'django.db.models.ImageField', args, kwargs
