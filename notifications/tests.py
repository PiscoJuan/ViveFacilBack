from unittest import mock

from django.contrib import admin, messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, SimpleTestCase
from fcm_django.models import FCMDevice
from firebase_admin.messaging import UnregisteredError

from notifications.admin import DispositivoNotificacionAdmin


def _request():
    request = RequestFactory().post("/admin/fcm_django/fcmdevice/")
    setattr(request, "session", {})
    setattr(request, "_messages", FallbackStorage(request))
    return request


class SendMessagesAdminTests(SimpleTestCase):
    """Un token muerto devolvía 500 en el admin (UnregisteredError sin atrapar)."""

    def setUp(self):
        self.admin = DispositivoNotificacionAdmin(FCMDevice, admin.site)

    def _device(self, activo_despues_del_error):
        device = mock.Mock(spec=["send_message", "refresh_from_db", "registration_id", "active"])
        device.registration_id = "cKq3f9TokenLargoDePrueba"
        device.send_message.side_effect = UnregisteredError("NotRegistered")
        device.active = True

        def _refresh(fields=None):
            device.active = activo_despues_del_error

        device.refresh_from_db.side_effect = _refresh
        return device

    def test_token_muerto_no_revienta_y_avisa_de_la_baja(self):
        request = _request()

        self.admin.send_messages(request, [self._device(activo_despues_del_error=False)])

        avisos = list(request._messages)
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0].level, messages.WARNING)
        self.assertIn("dados de baja por token inválido", avisos[0].message)

    def test_error_que_no_desactiva_se_reporta_aparte(self):
        request = _request()

        self.admin.send_messages(request, [self._device(activo_despues_del_error=True)])

        avisos = list(request._messages)
        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0].level, messages.ERROR)
        self.assertIn("siguen activos", avisos[0].message)
