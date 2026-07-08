"""
Chequeo del cálculo de montos (lo que realmente se cobra a la tarjeta).
Es la parte más sensible: un error acá cobra de más o de menos.

Correr:  python manage.py test pagos
"""
from decimal import Decimal

from django.test import SimpleTestCase

from pagos.services.pago_controller import _montos


class MontosTest(SimpleTestCase):
    def test_sin_descuento(self):
        m = _montos(Decimal("100"), 0)
        self.assertEqual(m["amount"], Decimal("100.00"))
        self.assertEqual(m["taxable_amount"], Decimal("86.96"))
        self.assertEqual(m["vat"], Decimal("13.04"))
        # el neto + iva reconstruye el bruto cobrado
        self.assertEqual(m["taxable_amount"] + m["vat"], m["amount"])

    def test_con_descuento_15(self):
        m = _montos(Decimal("100"), 15)  # base 85.00
        self.assertEqual(m["amount"], Decimal("85.00"))
        self.assertEqual(m["taxable_amount"], Decimal("73.91"))
        self.assertEqual(m["vat"], Decimal("11.09"))
        self.assertEqual(m["taxable_amount"] + m["vat"], m["amount"])

    def test_descuento_clamp_no_negativo(self):
        # 100% de descuento => amount 0, nunca negativo
        m = _montos(Decimal("50"), 100)
        self.assertEqual(m["amount"], Decimal("0.00"))
        self.assertGreaterEqual(m["amount"], Decimal("0.00"))
