"""Chequeo del enlace de recuperación: que el token valide, que sea de un solo
uso y que la página reaccione a cada caso.

    python manage.py test accounts.tests_password

Todo va sobre `SimpleTestCase` y con el ORM mockeado a propósito: el historial
de migraciones del proyecto no levanta una base de tests desde cero (la FK de
MovimientoPuntos contra el `api_datos` legacy y el choque de `api`/`accounts`
por la misma tabla), así que un TestCase con base de datos no correría acá.
Lo que interesa verificar igual no toca la base: la firma del token y los tres
estados de la vista.
"""
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import SimpleTestCase

from accounts import services


def _partes(url):
    """.../cuenta/cambiar-contrasena/<uid>/<token>/ -> (uid, token)"""
    return tuple(url.rstrip("/").split("/")[-2:])


def _usuario_en_memoria():
    # Sin guardar: make_token solo lee pk, password y last_login.
    return User(pk=7, username="alguien@vivefacil.app", email="alguien@vivefacil.app",
                password="pbkdf2_sha256$260000$sal$hashviejo", last_login=None)


class TokenRecuperacionTests(SimpleTestCase):
    def test_el_enlace_recien_generado_identifica_al_usuario(self):
        usuario = _usuario_en_memoria()
        uid, token = _partes(services._url_cambio_password(usuario))
        with patch.object(User.objects, "get", return_value=usuario):
            self.assertIs(services.usuario_por_token_recuperacion(uid, token), usuario)

    def test_token_manipulado_no_valida(self):
        usuario = _usuario_en_memoria()
        uid, token = _partes(services._url_cambio_password(usuario))
        with patch.object(User.objects, "get", return_value=usuario):
            self.assertIsNone(services.usuario_por_token_recuperacion(uid, token[:-1] + "x"))

    def test_al_cambiar_la_password_el_enlace_queda_quemado(self):
        usuario = _usuario_en_memoria()
        uid, token = _partes(services._url_cambio_password(usuario))
        usuario.password = "pbkdf2_sha256$260000$sal$hashnuevo"
        with patch.object(User.objects, "get", return_value=usuario):
            self.assertIsNone(services.usuario_por_token_recuperacion(uid, token))


class PaginaCambioTests(SimpleTestCase):
    url = "/cuenta/cambiar-contrasena/Nw/token-cualquiera/"

    def setUp(self):
        self.usuario = _usuario_en_memoria()
        parche = patch("accounts.services.nombre_para_saludo", return_value="Brayan")
        parche.start()
        self.addCleanup(parche.stop)

    def _con_enlace_valido(self):
        return patch("accounts.services.usuario_por_token_recuperacion", return_value=self.usuario)

    def test_enlace_invalido_no_muestra_el_formulario(self):
        with patch("accounts.services.usuario_por_token_recuperacion", return_value=None):
            self.assertContains(self.client.get(self.url), "NO VÁLIDO")
            # Y tampoco deja cambiar nada por POST directo.
            with patch("accounts.services.cambiar_password_usuario") as cambiar:
                self.assertContains(self.client.post(self.url, {"password1": "x", "password2": "x"}), "NO VÁLIDO")
                cambiar.assert_not_called()

    def test_enlace_valido_muestra_el_formulario(self):
        with self._con_enlace_valido():
            self.assertContains(self.client.get(self.url), "ELIGE TU NUEVA")

    def test_password_correcta_se_guarda(self):
        with self._con_enlace_valido(), \
             patch("accounts.services.cambiar_password_usuario", return_value=(True, "ok")) as cambiar:
            resp = self.client.post(self.url, {"password1": "claveNueva#2026", "password2": "claveNueva#2026"})
        self.assertContains(resp, "ACTUALIZADA")
        cambiar.assert_called_once_with(7, "claveNueva#2026")

    def test_passwords_distintas_no_guardan_nada(self):
        with self._con_enlace_valido(), \
             patch("accounts.services.cambiar_password_usuario") as cambiar:
            resp = self.client.post(self.url, {"password1": "claveNueva#2026", "password2": "otraCosa#2026"})
        self.assertContains(resp, "no coinciden")
        cambiar.assert_not_called()

    def test_password_debil_no_guarda_nada(self):
        with self._con_enlace_valido(), \
             patch("accounts.services.cambiar_password_usuario") as cambiar:
            resp = self.client.post(self.url, {"password1": "12345", "password2": "12345"})
        self.assertContains(resp, "ELIGE TU NUEVA")  # vuelve al formulario con errores
        cambiar.assert_not_called()
