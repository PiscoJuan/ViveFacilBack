"""Borra de MEDIA_ROOT los archivos que ya no referencia ninguna fila.

Son los huérfanos acumulados desde antes de que los FileField borraran el
archivo anterior al reemplazarlo.

    python manage.py limpiar_media            # solo lista (dry-run)
    python manage.py limpiar_media --borrar
"""
import os
import time

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import FileField


class Command(BaseCommand):
    help = "Lista (o borra con --borrar) los archivos de MEDIA_ROOT que ninguna fila referencia."

    def add_arguments(self, parser):
        parser.add_argument('--borrar', action='store_true', help="Borra de verdad. Sin esto solo lista.")
        parser.add_argument(
            '--dias', type=int, default=1,
            help="No toca archivos modificados en los últimos N días (subidas en curso). Por defecto 1.")

    def handle(self, *args, **opciones):
        referenciados = self._rutas_referenciadas()
        self.stdout.write(f"{len(referenciados)} archivos referenciados en la base.")

        corte = time.time() - opciones['dias'] * 86400
        huerfanos, bytes_totales = [], 0
        for carpeta, _, archivos in os.walk(settings.MEDIA_ROOT):
            for archivo in archivos:
                absoluta = os.path.join(carpeta, archivo)
                relativa = os.path.relpath(absoluta, settings.MEDIA_ROOT).replace('\\', '/')
                if relativa in referenciados or os.path.getmtime(absoluta) > corte:
                    continue
                huerfanos.append((absoluta, relativa))
                bytes_totales += os.path.getsize(absoluta)

        for _, relativa in huerfanos:
            self.stdout.write(relativa)

        resumen = f"{len(huerfanos)} huérfanos, {bytes_totales / 1048576:.1f} MB"
        if not opciones['borrar']:
            self.stdout.write(self.style.WARNING(f"{resumen}. Dry-run: no se borró nada (usá --borrar)."))
            return

        borrados = 0
        for absoluta, relativa in huerfanos:
            try:
                os.remove(absoluta)
                borrados += 1
            except OSError as e:
                self.stderr.write(f"No se pudo borrar {relativa}: {e}")
        self.stdout.write(self.style.SUCCESS(f"{borrados}/{len(huerfanos)} borrados ({resumen})."))

    def _rutas_referenciadas(self):
        rutas = set()
        for modelo in apps.get_models():
            campos = [c.attname for c in modelo._meta.concrete_fields if isinstance(c, FileField)]
            if not campos:
                continue
            for fila in modelo._base_manager.values_list(*campos):
                rutas.update(v for v in fila if v)
        return rutas
