import os

from django.core.files import File
from django.core.files.storage import default_storage


def ruta_relativa(nombre):
    """Hay filas viejas que guardaron la URL completa en la columna en vez de
    la ruta relativa a MEDIA_ROOT. Pasarle eso al storage revienta con
    SuspiciousFileOperation, así que siempre se normaliza antes de tocarlo."""
    return nombre.split('/media/', 1)[-1] if nombre else nombre


def copiar_desde_media(ruta):
    """Copia el archivo que vive en `ruta` (relativa a MEDIA_ROOT, o una URL
    completa con /media/) para asignarlo a otro FileField.

    Sin esto, asignar la ruta pelada deja dos filas apuntando al mismo archivo
    y borrar una se lleva el archivo de la otra. Si el archivo no está, se
    devuelve la ruta tal cual para no cambiar el comportamiento previo.
    """
    if not ruta:
        return None
    ruta = ruta_relativa(ruta)
    if not default_storage.exists(ruta):
        return ruta
    return File(default_storage.open(ruta), os.path.basename(ruta))
