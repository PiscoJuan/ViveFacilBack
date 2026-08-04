"""Que el aviso de chat no reporte error cuando el destinatario simplemente no
tiene dispositivos registrados (el mensaje ya viajó por Firebase; esto es solo
el push).

    python manage.py test notifications.tests_chat_push

`SimpleTestCase` con el ORM mockeado: este proyecto no puede construir una base
de tests desde cero (ver accounts/tests_password.py).
"""
from unittest.mock import patch

from django.test import SimpleTestCase

from notifications import services


class _Datos:
    id = 12
    nombres = "Brayan"
    user_id = 634


class _Solicitante:
    user_datos_id = 99


def _mock_orm(tokens):
    """Deja el camino feliz de la función con los `tokens` que se le pasen."""
    devices = patch("fcm_django.models.FCMDevice.objects")
    datos = patch("notifications.services.Datos.objects")
    soli = patch("notifications.services.Solicitante.objects")
    m_dev, m_datos, m_soli = devices.start(), datos.start(), soli.start()
    m_datos.get.return_value = _Datos()
    m_soli.get.return_value = _Solicitante()
    m_dev.filter.return_value.values_list.return_value = tokens
    return (devices, datos, soli)


class AvisoChatProveedorTests(SimpleTestCase):
    def _llamar(self, tokens):
        parches = _mock_orm(tokens)
        try:
            with patch("core.firebase.send_notificationF") as enviar:
                data, status = services.notificar_chat_proveedor(1, 2, "hola", "/chat-texto/1")
            return data, status, enviar
        finally:
            for p in parches:
                p.stop()

    def test_sin_dispositivos_contesta_200_y_no_intenta_enviar(self):
        data, status, enviar = self._llamar([])
        self.assertEqual(status, 200)          # antes: 404 -> error rojo en la app
        self.assertFalse(data["enviado"])
        enviar.assert_not_called()

    def test_con_dispositivos_envia_y_contesta_200(self):
        data, status, enviar = self._llamar(["token-abc"])
        self.assertEqual(status, 200)
        self.assertTrue(data["enviado"])
        enviar.assert_called_once()
        self.assertEqual(enviar.call_args.args[0], ["token-abc"])

    def test_ids_inexistentes_siguen_siendo_404(self):
        with patch("notifications.services.Datos.objects") as m_datos:
            from accounts.models import Datos
            m_datos.get.side_effect = Datos.DoesNotExist
            data, status = services.notificar_chat_proveedor(1, 2, "hola", "/x")
        self.assertEqual(status, 404)
        self.assertIn("error", data)
