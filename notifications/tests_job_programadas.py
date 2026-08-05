"""Cuándo dispara una notificación programada.

    python manage.py test notifications.tests_job_programadas

`debe_disparar` es duck-typed y recibe el tiempo por parámetro, así que se
prueba entero sin ORM ni reloj real.
"""
from datetime import datetime, time, timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from notifications import services
from notifications.models import FRECUENCIA_DIARIA, FRECUENCIA_SEMANAL, FRECUENCIA_UNICA


class _Notif:
    """Lo mínimo que mira `debe_disparar`."""

    def __init__(self, **kwargs):
        self.hora = time(10, 0)
        self.frecuencia = FRECUENCIA_DIARIA
        self.dias_semana = ''
        self.veces_enviada = 0
        self.ultimo_envio = None
        self.fecha_iniciacion = None
        self.fecha_expiracion = None
        self.__dict__.update(kwargs)


def _momento(anio, mes, dia, hh, mm=0):
    return timezone.make_aware(datetime(anio, mes, dia, hh, mm), timezone.get_current_timezone())


# 2026-08-05 es miércoles -> weekday() == 2
MIERCOLES = _momento(2026, 8, 5, 11, 0)
HOY = MIERCOLES.date()


class DebeDispararTests(SimpleTestCase):
    def test_dispara_cuando_su_hora_ya_paso(self):
        self.assertIsNotNone(services.debe_disparar(_Notif(), MIERCOLES, HOY))

    def test_no_dispara_si_su_hora_es_mas_tarde(self):
        notif = _Notif(hora=time(23, 30))
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_sin_hora_no_dispara(self):
        self.assertIsNone(services.debe_disparar(_Notif(hora=None), MIERCOLES, HOY))

    def test_unica_ya_enviada_no_se_repite(self):
        notif = _Notif(frecuencia=FRECUENCIA_UNICA, veces_enviada=1)
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_unica_sin_enviar_dispara(self):
        notif = _Notif(frecuencia=FRECUENCIA_UNICA, veces_enviada=0)
        self.assertIsNotNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_semanal_en_dia_que_no_toca(self):
        notif = _Notif(frecuencia=FRECUENCIA_SEMANAL, dias_semana='0,4')  # lunes y viernes
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_semanal_en_dia_que_si_toca(self):
        notif = _Notif(frecuencia=FRECUENCIA_SEMANAL, dias_semana='0,2,4')  # incluye miércoles
        self.assertIsNotNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_semanal_sin_dias_no_dispara_nunca(self):
        notif = _Notif(frecuencia=FRECUENCIA_SEMANAL, dias_semana='')
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_ya_enviada_en_este_slot_no_se_duplica(self):
        notif = _Notif(ultimo_envio=_momento(2026, 8, 5, 10, 0))
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_job_caido_tres_dias_dispara_una_sola_vez(self):
        """Al volver de una caída no debe salir una push por cada día perdido:
        solo cuenta el slot de hoy."""
        notif = _Notif(ultimo_envio=_momento(2026, 8, 2, 10, 0))
        slot = services.debe_disparar(notif, MIERCOLES, HOY)
        self.assertEqual(slot, _momento(2026, 8, 5, 10, 0))

    def test_antes_de_la_fecha_de_inicio_no_dispara(self):
        notif = _Notif(fecha_iniciacion=MIERCOLES + timedelta(days=1))
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_despues_de_la_fecha_de_expiracion_no_dispara(self):
        notif = _Notif(fecha_expiracion=MIERCOLES - timedelta(days=1))
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_frecuencia_legacy_no_dispara(self):
        """Texto libre de antes de la migración: no adivinar, no disparar."""
        notif = _Notif(frecuencia='Una vez al día')
        self.assertIsNone(services.debe_disparar(notif, MIERCOLES, HOY))

    def test_el_slot_devuelto_es_aware(self):
        slot = services.debe_disparar(_Notif(), MIERCOLES, HOY)
        self.assertIsNotNone(slot.tzinfo)
