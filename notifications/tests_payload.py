"""El `data` del push debe ser todo strings: FCM v1 rechaza el mensaje entero
si algún valor no lo es, y los campos del modelo son nullable.

    python manage.py test notifications.tests_payload
"""
from django.test import SimpleTestCase

from notifications import services


class _Imagen:
    url = 'http://host/media/notificaciones/x.png'

    def __bool__(self):
        return True


class _Notif:
    def __init__(self, ruta='/main/home', descripcion='hola', imagen=None):
        self.ruta = ruta
        self.descripcion = descripcion
        self.imagen = imagen


class PayloadTests(SimpleTestCase):
    def test_todos_los_valores_son_strings(self):
        data = services._payload(_Notif(imagen=_Imagen()))
        self.assertTrue(all(isinstance(v, str) for v in data.values()), data)

    def test_campos_nulos_salen_como_cadena_vacia(self):
        data = services._payload(_Notif(ruta=None, descripcion=None))
        self.assertEqual(data['ruta'], '')
        self.assertEqual(data['descripcion'], '')

    def test_sin_imagen_no_incluye_la_clave(self):
        self.assertNotIn('imagen', services._payload(_Notif()))

    def test_con_imagen_manda_la_url(self):
        data = services._payload(_Notif(imagen=_Imagen()))
        self.assertEqual(data['imagen'], _Imagen.url)
