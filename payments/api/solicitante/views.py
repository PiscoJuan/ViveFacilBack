from rest_framework.response import Response

from api.serializers import PagoEfectivoSerializer
from core.views import SolicitanteAPIView
from payments import services


class PagoEfectivoSolicitanteView(SolicitanteAPIView):
    def post(self, request, format=None):
        pago_efectivo, data = services.registrar_pago_efectivo(request.data)
        if pago_efectivo is not None:
            data["pago_efectivo"] = PagoEfectivoSerializer(pago_efectivo).data
        return Response(data)


class EmailFacturaSolicitanteView(SolicitanteAPIView):
    """Recibo por correo del pago en efectivo (`pagarConEfectivo` en el
    frontend). El pago con tarjeta ya no lo llama: el backend envía el
    recibo automáticamente al confirmar la transacción con Paymentez."""

    def post(self, request, format=None):
        return Response(services.enviar_email_factura(request.data))
