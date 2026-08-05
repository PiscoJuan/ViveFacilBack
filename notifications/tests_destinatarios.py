"""Regla de a quién le llega cada notificación.

    python manage.py test notifications.tests_destinatarios

`condicion_destinatarios` es pura y devuelve un `Q`, así que se inspecciona
directamente sin mocks ni base de datos (este proyecto no puede crear una de
tests; ver accounts/tests_password.py).
"""
from django.test import SimpleTestCase

from notifications import services
from notifications.models import DIRIGIDA_AMBAS, DIRIGIDA_PROVEEDOR, DIRIGIDA_SOLICITANTE


def _lookups(q):
    """Todos los lookups de un Q, aplanando los Q anidados."""
    encontrados = []
    for hijo in q.children:
        if hasattr(hijo, 'children'):
            encontrados.extend(_lookups(hijo))
        else:
            encontrados.append(hijo[0])
    return encontrados


class CondicionDestinatariosTests(SimpleTestCase):
    def test_ambas_incluye_proveedores_y_solicitantes(self):
        lookups = _lookups(services.condicion_destinatarios(DIRIGIDA_AMBAS, []))
        self.assertIn('proveedor__estado', lookups)
        self.assertIn('solicitante__estado', lookups)

    def test_solo_proveedor_excluye_solicitantes(self):
        lookups = _lookups(services.condicion_destinatarios(DIRIGIDA_PROVEEDOR, []))
        self.assertIn('proveedor__estado', lookups)
        self.assertNotIn('solicitante__estado', lookups)

    def test_solo_solicitante_excluye_proveedores(self):
        lookups = _lookups(services.condicion_destinatarios(DIRIGIDA_SOLICITANTE, []))
        self.assertIn('solicitante__estado', lookups)
        self.assertNotIn('proveedor__estado', lookups)

    def test_proveedor_con_profesiones_filtra_por_la_pivote(self):
        lookups = _lookups(services.condicion_destinatarios(DIRIGIDA_PROVEEDOR, [3, 7]))
        # Vía Profesion_Proveedor, nunca el CSV Proveedor.profesion.
        self.assertIn('proveedor__profesion_proveedor__profesion_id__in', lookups)
        self.assertIn('proveedor__profesion_proveedor__estado', lookups)

    def test_proveedor_sin_profesiones_no_filtra_por_profesion(self):
        """Sin profesiones configuradas la notificación es para todos los
        proveedores, no para ninguno."""
        lookups = _lookups(services.condicion_destinatarios(DIRIGIDA_PROVEEDOR, []))
        self.assertFalse(any('profesion' in lk for lk in lookups))

    def test_solicitante_ignora_las_profesiones(self):
        lookups = _lookups(services.condicion_destinatarios(DIRIGIDA_SOLICITANTE, [3, 7]))
        self.assertFalse(any('profesion' in lk for lk in lookups))

    def test_dirigida_a_nulo_se_trata_como_ambas(self):
        """Filas legacy anteriores a la migración."""
        lookups = _lookups(services.condicion_destinatarios(None, []))
        self.assertIn('proveedor__estado', lookups)
        self.assertIn('solicitante__estado', lookups)
