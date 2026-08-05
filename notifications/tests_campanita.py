"""Filtrado de la lista de notificaciones que ve cada app.

    python manage.py test notifications.tests_campanita

Se mockea el ORM y se inspeccionan los kwargs con los que se llamó a `filter`,
que es donde vive la regla.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from notifications import services
from notifications.models import DIRIGIDA_AMBAS, DIRIGIDA_PROVEEDOR, DIRIGIDA_SOLICITANTE


class _Tipo:
    def __init__(self, name):
        self.name = name


class _Datos:
    def __init__(self, rol):
        self.tipo = _Tipo(rol) if rol else None
        self.fecha_creacion = datetime(2025, 1, 1)


class CampanitaTests(SimpleTestCase):
    def _consultar(self, rol):
        """Devuelve la lista de kwargs con que se encadenaron los filter()."""
        qs = MagicMock()
        qs.filter.return_value = qs
        qs.prefetch_related.return_value = qs
        qs.distinct.return_value = qs
        qs.order_by.return_value = qs

        datos = _Datos(rol) if rol else None

        with patch.object(services, 'Datos') as m_datos, \
                patch('notifications.models.NotificacionMasiva.objects', qs), \
                patch('catalog.models.Profesion_Proveedor.objects', MagicMock()):
            m_datos.objects.filter.return_value.select_related.return_value.first.return_value = datos
            resultado = services.notificaciones_visibles(user=MagicMock())

        kwargs = [c.kwargs for c in qs.filter.call_args_list]
        return resultado, kwargs, qs

    def test_sin_datos_devuelve_vacio(self):
        """Un usuario sin fila en Datos no ve nada, en vez de reventar."""
        qs = MagicMock()
        with patch.object(services, 'Datos') as m_datos, \
                patch('notifications.models.NotificacionMasiva.objects', qs):
            m_datos.objects.filter.return_value.select_related.return_value.first.return_value = None
            services.notificaciones_visibles(user=MagicMock())
        qs.none.assert_called_once()

    def test_siempre_filtra_por_enviadas_y_activas(self):
        _, kwargs, _ = self._consultar('Solicitante')
        base = kwargs[0]
        self.assertTrue(base['estado'])
        self.assertFalse(base['enviada_en__isnull'])

    def test_siempre_filtra_por_fecha_de_registro(self):
        """Criterio 1: nada anterior al alta del usuario, medido por la fecha
        de ENVÍO."""
        _, kwargs, _ = self._consultar('Proveedor')
        fechas = [k['enviada_en__gte'] for k in kwargs if 'enviada_en__gte' in k]
        self.assertEqual(fechas, [datetime(2025, 1, 1)])

    def test_proveedor_ve_ambas_y_proveedor(self):
        _, kwargs, _ = self._consultar('Proveedor')
        destinos = [k['dirigida_a__in'] for k in kwargs if 'dirigida_a__in' in k]
        self.assertEqual(destinos, [[DIRIGIDA_AMBAS, DIRIGIDA_PROVEEDOR]])

    def test_solicitante_ve_ambas_y_solicitante(self):
        _, kwargs, _ = self._consultar('Solicitante')
        destinos = [k['dirigida_a__in'] for k in kwargs if 'dirigida_a__in' in k]
        self.assertEqual(destinos, [[DIRIGIDA_AMBAS, DIRIGIDA_SOLICITANTE]])

    def test_solo_el_proveedor_pasa_por_el_filtro_de_profesion(self):
        """El Q de profesiones va posicional, no en kwargs: se cuenta cuántos
        filter() llevaron argumentos posicionales."""
        _, _, qs_prov = self._consultar('Proveedor')
        con_q_prov = sum(1 for c in qs_prov.filter.call_args_list if c.args)

        _, _, qs_soli = self._consultar('Solicitante')
        con_q_soli = sum(1 for c in qs_soli.filter.call_args_list if c.args)

        self.assertEqual(con_q_prov, 1)
        self.assertEqual(con_q_soli, 0)
