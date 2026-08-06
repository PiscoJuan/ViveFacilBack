"""Feed combinado de la pestaña Notificaciones: masivas + eventos
individuales, mezclados, con leído/no-leído y "eliminar" por usuario.

    python manage.py test notifications.tests_feed

Sin base de datos de tests disponible (ver notifications/tests_destinatarios.py):
se mockea el ORM, siguiendo el patrón de notifications/tests_job_masivas.py.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from notifications import services


class _Masiva:
    def __init__(self, id, titulo, enviada_en):
        self.id = id
        self.titulo = titulo
        self.descripcion = 'desc masiva'
        self.imagen = None
        self.ruta = ''
        self.enviada_en = enviada_en


class _Estado:
    def __init__(self, notificacion_id, leida_en=None, oculta=False):
        self.notificacion_id = notificacion_id
        self.leida_en = leida_en
        self.oculta = oculta


class _Individual:
    def __init__(self, id, titulo, fecha_creacion, leida_en=None, tipo='cupon'):
        self.id = id
        self.tipo = tipo
        self.titulo = titulo
        self.descripcion = 'desc individual'
        self.imagen = None
        self.ruta = ''
        self.fecha_creacion = fecha_creacion
        self.leida_en = leida_en


class FeedNotificacionesTests(SimpleTestCase):
    def _correr(self, masivas, estados, individuales):
        user = MagicMock()
        with patch.object(services, 'notificaciones_visibles', return_value=masivas), \
                patch.object(services, 'NotificacionMasivaEstado') as estado_modelo, \
                patch.object(services, 'NotificacionIndividual') as individual_modelo:
            estado_modelo.objects.filter.return_value = estados
            individual_modelo.objects.filter.return_value = individuales
            return services.feed_notificaciones(user)

    def test_mezcla_masivas_e_individuales_por_fecha(self):
        masivas = [_Masiva(1, 'Masiva vieja', datetime(2026, 1, 1))]
        individuales = [_Individual(10, 'Individual nueva', datetime(2026, 6, 1))]
        items, counts = self._correr(masivas, [], individuales)

        self.assertEqual([it['titulo'] for it in items], ['Individual nueva', 'Masiva vieja'])
        self.assertEqual(counts['todas'], 2)

    def test_masiva_oculta_no_aparece(self):
        masivas = [_Masiva(1, 'Oculta', datetime(2026, 1, 1)), _Masiva(2, 'Visible', datetime(2026, 1, 2))]
        estados = [_Estado(notificacion_id=1, oculta=True)]
        items, counts = self._correr(masivas, estados, [])

        self.assertEqual([it['titulo'] for it in items], ['Visible'])
        self.assertEqual(counts['todas'], 1)

    def test_individual_oculta_se_filtra_en_la_query_no_en_python(self):
        """`ocultar_notificacion` marca `oculta=True`; el filtro real vive en
        el `.filter(oculta=False)` de la query (mockeada acá), así que el
        service ni siquiera la ve — esto solo confirma que no revienta si la
        query ya viene sin ocultas."""
        items, counts = self._correr([], [], [])
        self.assertEqual(items, [])
        self.assertEqual(counts, {'todas': 0, 'no_leidas': 0, 'leidas': 0})

    def test_contadores_leidas_no_leidas(self):
        masivas = [_Masiva(1, 'A', datetime(2026, 1, 1)), _Masiva(2, 'B', datetime(2026, 1, 2))]
        estados = [_Estado(notificacion_id=1, leida_en=datetime(2026, 1, 3))]
        items, counts = self._correr(masivas, estados, [])

        self.assertEqual(counts, {'todas': 2, 'no_leidas': 1, 'leidas': 1})
        by_id = {it['id']: it['leida'] for it in items}
        self.assertTrue(by_id[1])
        self.assertFalse(by_id[2])


class MarcarLeidaOcultarTests(SimpleTestCase):
    def test_marcar_leida_tipo_invalido_lanza(self):
        with self.assertRaises(ValueError):
            services.marcar_leida(MagicMock(), 'lo-que-sea', 1)

    def test_ocultar_tipo_invalido_lanza(self):
        with self.assertRaises(ValueError):
            services.ocultar_notificacion(MagicMock(), 'lo-que-sea', 1)

    def test_marcar_leida_masiva_usa_get_or_create(self):
        user = MagicMock()
        with patch.object(services, 'NotificacionMasivaEstado') as modelo:
            estado = MagicMock(leida_en=None)
            modelo.objects.get_or_create.return_value = (estado, True)
            services.marcar_leida(user, 'masiva', 5)
            modelo.objects.get_or_create.assert_called_once_with(notificacion_id=5, user=user)
            estado.save.assert_called_once()

    def test_ocultar_individual_actualiza_por_id_y_usuario(self):
        user = MagicMock()
        with patch.object(services, 'NotificacionIndividual') as modelo:
            services.ocultar_notificacion(user, 'individual', 7)
            modelo.objects.filter.assert_called_once_with(id=7, user=user)
            modelo.objects.filter.return_value.update.assert_called_once_with(oculta=True)
