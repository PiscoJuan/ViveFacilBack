"""Repara la desincronización entre `api_proveedor.profesion` (texto libre) y
`api_profesion_proveedor` (la relación real que alimenta la lista de
proveedores por sub-categoría en el admin).

Un proveedor puede tener 'Albañil' en su ficha y NO aparecer bajo la
sub-categoría Albañil, porque son dos fuentes de verdad distintas y el PUT de
editar proveedor (accounts/services.py) borra todas las filas y las recrea
sólo con match exacto de nombre — lo que no calza se pierde en silencio.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Proveedor
from catalog.models import Profesion, Profesion_Proveedor


class Command(BaseCommand):
    help = (
        "Crea las filas faltantes en Profesion_Proveedor a partir del texto de "
        "Proveedor.profesion, y quita espacios sobrantes en Profesion.nombre. "
        "Por defecto sólo reporta: usar --apply para escribir."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Escribe los cambios. Sin este flag el comando es de sólo lectura.",
        )
        parser.add_argument(
            "--proveedor",
            type=int,
            default=None,
            help="Limita la reparación a un id de Proveedor.",
        )

    def handle(self, *args, **options):
        aplicar = options["apply"]
        solo_id = options["proveedor"]

        with transaction.atomic():
            renombradas = self._limpiar_nombres_profesion()
            creadas, sin_profesion = self._crear_filas_faltantes(solo_id)

            if not aplicar:
                # ponytail: rollback en vez de duplicar la lógica en un modo
                # "simulación" — el reporte sale idéntico y nada queda escrito.
                transaction.set_rollback(True)

        for viejo, nuevo in renombradas:
            self.stdout.write(f"Profesion renombrada: {viejo!r} -> {nuevo!r}")
        for proveedor_id, nombre in creadas:
            self.stdout.write(f"Profesion_Proveedor creada: proveedor={proveedor_id} profesion={nombre!r}")
        for proveedor_id, nombre in sin_profesion:
            self.stdout.write(
                self.style.WARNING(
                    f"Sin Profesion homónima: proveedor={proveedor_id} texto={nombre!r} (requiere crearla a mano)"
                )
            )

        resumen = (
            f"{len(renombradas)} profesion(es) renombrada(s), "
            f"{len(creadas)} fila(s) creada(s), "
            f"{len(sin_profesion)} sin profesión homónima."
        )
        if aplicar:
            self.stdout.write(self.style.SUCCESS("APLICADO. " + resumen))
        else:
            self.stdout.write(self.style.WARNING("SIMULACIÓN (nada escrito). " + resumen))
            self.stdout.write("Volver a correr con --apply para escribir.")

    def _limpiar_nombres_profesion(self):
        """Hay Profesion guardadas con espacio al final ('Catering Alimentos '),
        que nunca calzan con el texto del proveedor."""
        renombradas = []
        for profesion in Profesion.objects.all():
            limpio = (profesion.nombre or "").strip()
            if limpio and limpio != profesion.nombre:
                renombradas.append((profesion.nombre, limpio))
                profesion.nombre = limpio
                profesion.save(update_fields=["nombre"])
        return renombradas

    def _crear_filas_faltantes(self, solo_id):
        creadas, sin_profesion = [], []

        proveedores = Proveedor.objects.exclude(profesion="").exclude(profesion=None)
        if solo_id is not None:
            proveedores = proveedores.filter(id=solo_id)

        # Se re-consulta por nombre limpio, ya normalizado arriba.
        por_nombre = {p.nombre: p for p in Profesion.objects.all()}

        for proveedor in proveedores:
            existentes = set(
                Profesion_Proveedor.objects.filter(proveedor=proveedor).values_list("profesion__nombre", flat=True)
            )
            for nombre in {t.strip() for t in proveedor.profesion.split(",") if t.strip()}:
                if nombre in existentes:
                    continue
                profesion = por_nombre.get(nombre)
                if profesion is None:
                    sin_profesion.append((proveedor.id, nombre))
                    continue
                Profesion_Proveedor.objects.create(
                    proveedor=proveedor,
                    profesion=profesion,
                    ano_experiencia=_anios(proveedor.ano_profesion),
                )
                creadas.append((proveedor.id, nombre))

        return creadas, sin_profesion


def _anios(valor):
    """`Proveedor.ano_profesion` es CharField y trae basura ('', '10 años')."""
    try:
        return max(0, int(str(valor).strip()))
    except (TypeError, ValueError):
        return 0
