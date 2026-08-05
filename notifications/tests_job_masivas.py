"""El claim atómico que evita envíos duplicados de las masivas.

    python manage.py test notifications.tests_job_masivas

Lo que se prueba es que el envío depende del resultado del UPDATE condicional,
que es lo que hace de lock cuando dos ejecuciones del cron se solapan.
"""
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from notifications.management.commands import enviar_notificaciones_programadas as cmd_mod


class _Notif:
    pk = 42
    titulo = 'Promo'


class ClaimMasivasTests(SimpleTestCase):
    def _correr(self, filas_actualizadas):
        """Deja el manager mockeado y devuelve (enviadas, mock de enviar_push)."""
        manager = MagicMock()
        pendientes = MagicMock(__iter__=lambda self: iter([_Notif()]))
        claim = MagicMock()
        claim.update.return_value = filas_actualizadas
        # Los dos filter() en orden: el de pendientes y el del claim atómico.
        manager.filter.side_effect = [pendientes, claim]

        comando = cmd_mod.Command()
        comando.stdout = MagicMock()
        with patch.object(cmd_mod, 'NotificacionMasiva') as modelo, \
                patch.object(cmd_mod.services, 'enviar_push', return_value=3) as enviar:
            modelo.objects = manager
            enviadas = comando._enviar_masivas(ahora='2026-08-05')
        return enviadas, enviar

    def test_claim_ganado_envia_una_vez(self):
        enviadas, enviar = self._correr(filas_actualizadas=1)
        self.assertEqual(enviadas, 1)
        enviar.assert_called_once()

    def test_claim_perdido_no_envia(self):
        """Otro proceso ya la reclamó: el UPDATE afecta 0 filas y no se manda
        nada. Es lo que hace idempotente al job si el cron se solapa."""
        enviadas, enviar = self._correr(filas_actualizadas=0)
        self.assertEqual(enviadas, 0)
        enviar.assert_not_called()
