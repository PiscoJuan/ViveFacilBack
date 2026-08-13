"""borrar_cuenta_firebase: True si la borró, False si la cuenta no existía.

    python manage.py test core.tests_firebase_auth
"""
import sys
from unittest import mock

from django.test import SimpleTestCase

# Importado acá y no dentro del patch.dict: si core.firebase entrara a
# sys.modules dentro del parche, al salir se descartaría y el resto de la suite
# terminaría con dos copias del módulo (parchear una no afecta a la otra).
from core.firebase import borrar_cuenta_firebase


class _UserNotFoundError(Exception):
    pass


class BorrarCuentaFirebaseTests(SimpleTestCase):
    def _con_firebase(self, get_user_by_email):
        auth = mock.Mock(UserNotFoundError=_UserNotFoundError, get_user_by_email=get_user_by_email)
        firebase_admin = mock.Mock(_apps={'default': object()})
        modulos = {
            'firebase_admin': firebase_admin,
            'firebase_admin.auth': auth,
            'firebase_admin.credentials': mock.Mock(),
        }
        firebase_admin.auth = auth
        firebase_admin.credentials = modulos['firebase_admin.credentials']
        return mock.patch.dict(sys.modules, modulos), auth

    def test_borra_la_cuenta_existente(self):
        parche, auth = self._con_firebase(mock.Mock(return_value=mock.Mock(uid='abc123')))
        with parche:
            self.assertTrue(borrar_cuenta_firebase('alguien@mail.com'))
        auth.delete_user.assert_called_once_with('abc123')

    def test_devuelve_false_si_no_existe(self):
        parche, auth = self._con_firebase(mock.Mock(side_effect=_UserNotFoundError('no está')))
        with parche:
            self.assertFalse(borrar_cuenta_firebase('fantasma@mail.com'))
        auth.delete_user.assert_not_called()
