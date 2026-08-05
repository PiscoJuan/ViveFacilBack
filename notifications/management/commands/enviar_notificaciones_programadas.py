from django.core.management.base import BaseCommand
from django.db.models import F, Q
from django.utils import timezone

from notifications import services
from notifications.models import Notificacion, NotificacionMasiva


class Command(BaseCommand):
    help = (
        "Envía las notificaciones que tocan en este momento: las masivas con "
        "hora programada ya cumplida, y las programadas cuya recurrencia cae "
        "en el slot actual. Pensado para correr cada media hora (:00 y :30) "
        "como tarea programada de PythonAnywhere. Es idempotente: correrlo de "
        "más no duplica envíos."
    )

    def handle(self, *args, **options):
        ahora = timezone.localtime()
        hoy = timezone.localdate()

        masivas = self._enviar_masivas(ahora)
        programadas = self._enviar_programadas(ahora, hoy)

        self.stdout.write(self.style.SUCCESS(
            f"{masivas} masiva(s) y {programadas} programada(s) enviadas "
            f"({ahora:%d/%m/%Y %H:%M})."
        ))

    def _enviar_masivas(self, ahora):
        """Masivas con hora cumplida que todavía no salieron.

        El filtro es `<=`, no `==`: si el job no corrió a las 11:00, a las 11:30
        la recoge igual. Sigue enviándose una sola vez.
        """
        pendientes = NotificacionMasiva.objects.filter(
            estado=True,
            enviada_en__isnull=True,
            programada_para__isnull=False,
            programada_para__lte=ahora,
        )
        enviadas = 0
        for notif in pendientes:
            # Claim atómico: un único UPDATE condicional hace de lock. Si dos
            # ejecuciones se solapan, la segunda actualiza 0 filas y se salta la
            # notificación. Sin transacciones ni lockfile.
            if not NotificacionMasiva.objects.filter(
                    pk=notif.pk, enviada_en__isnull=True).update(enviada_en=ahora):
                continue
            tokens = services.enviar_push(notif)
            enviadas += 1
            self.stdout.write(f"Masiva #{notif.pk} '{notif.titulo}' -> {tokens} dispositivo(s).")
        return enviadas

    def _enviar_programadas(self, ahora, hoy):
        """Programadas cuya recurrencia cae en el slot actual.

        Si el job estuvo caído varios días, una recurrente dispara UNA vez al
        volver (el slot de hoy), no una por día perdido: no queremos una
        tormenta de pushes atrasados.
        """
        candidatas = Notificacion.objects.filter(estado=True, hora__isnull=False)
        enviadas = 0
        for notif in candidatas:
            slot = services.debe_disparar(notif, ahora, hoy)
            if slot is None:
                continue
            # Mismo claim atómico, y el contador sube en el propio UPDATE.
            # Se incrementa al reclamar y no tras el envío a propósito: si FCM
            # falla no queremos que la siguiente corrida lo reintente en bucle.
            reclamada = Notificacion.objects.filter(pk=notif.pk).filter(
                Q(ultimo_envio__isnull=True) | Q(ultimo_envio__lt=slot)
            ).update(ultimo_envio=ahora, veces_enviada=F('veces_enviada') + 1)
            if not reclamada:
                continue
            tokens = services.enviar_push(notif)
            enviadas += 1
            self.stdout.write(f"Programada #{notif.pk} '{notif.titulo}' -> {tokens} dispositivo(s).")
        return enviadas
