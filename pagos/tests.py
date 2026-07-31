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

    def test_caso_reportado_5_dolares(self):
        """El caso concreto del reporte: 5.00 se desglosa 4.35 + 0.65, no 5.00 + 0.75.
        Estos mismos números están replicados en el test del helper del front."""
        m = _montos(Decimal("5.00"), 0)
        self.assertEqual(m["amount"], Decimal("5.00"))
        self.assertEqual(m["taxable_amount"], Decimal("4.35"))
        self.assertEqual(m["vat"], Decimal("0.65"))

    def test_tasa_parametrizable(self):
        """La tasa es parámetro para el día en que haya proveedores con IVA 0."""
        m = _montos(Decimal("100"), 0, tax_pct=Decimal("0"))
        self.assertEqual(m["amount"], Decimal("100.00"))
        self.assertEqual(m["taxable_amount"], Decimal("100.00"))
        self.assertEqual(m["vat"], Decimal("0.00"))

        m12 = _montos(Decimal("112"), 0, tax_pct=Decimal("12"))
        self.assertEqual(m12["taxable_amount"], Decimal("100.00"))
        self.assertEqual(m12["vat"], Decimal("12.00"))

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


class PayloadPaymentezTest(SimpleTestCase):
    """A Paymentez se le declara IVA cero: el monto es el precio final y los
    campos fiscales van presentes pero en 0. El desglose real se guarda en
    nuestra BD, no viaja a la pasarela."""

    def _payload(self):
        from pagos.services.paymentez_client import PaymentezClient

        return PaymentezClient.build_payload_debit(
            PaymentezClient.__new__(PaymentezClient),
            user_id="u1", email="a@b.c", monto=Decimal("5.00"),
            descripcion="Solicitud 1", dev_reference="REF", card_token="tok",
            card_cvc="123",
        )

    def test_order_lleva_precio_final(self):
        self.assertEqual(self._payload()["order"]["amount"], 5.00)

    def test_order_declara_iva_cero(self):
        order = self._payload()["order"]
        # taxable_amount es la porción sujeta a impuesto: con IVA 0 es 0, no el
        # monto completo. Si esto se cambia, hay que cambiarlo a conciencia.
        for clave in ("vat", "taxable_amount", "tax_percentage"):
            self.assertIn(clave, order)
            self.assertEqual(order[clave], 0, f"{clave} debería ir en 0")
