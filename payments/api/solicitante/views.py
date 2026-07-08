from rest_framework.response import Response

from api.serializers import PagoEfectivoSerializer, PagoTarjetaSerializer, TarjetaSerializer
from core.views import SolicitanteAPIView
from payments import services


class PagoEfectivoSolicitanteView(SolicitanteAPIView):
    def post(self, request, format=None):
        pago_efectivo, data = services.registrar_pago_efectivo(request.data)
        if pago_efectivo is not None:
            data["pago_efectivo"] = PagoEfectivoSerializer(pago_efectivo).data
        return Response(data)


class PagoTarjetaSolicitanteView(SolicitanteAPIView):
    def post(self, request, format=None):
        pago_tarjeta, data = services.registrar_pago_tarjeta(request.data)
        if pago_tarjeta is not None:
            data["pago_tarjeta"] = PagoTarjetaSerializer(pago_tarjeta).data
        return Response(data)


class EmailFacturaSolicitanteView(SolicitanteAPIView):
    """page.ts`)."""

    def post(self, request, format=None):
        return Response(services.enviar_email_factura(request.data))


class TarjetaSolicitanteView(SolicitanteAPIView):
    """El GET (`list_tarjetas_todas`, devuelve TODAS las tarjetas sin filtrar)
    no tiene evidencia de llamador real en ningún frontend — preexistente,
    se migra igual por consistencia, no se corrige. El POST (crear tarjeta)
    sí está confirmado real, exclusivo de Solicitante2022."""

    def get(self, request, format=None):
        # Antes devolvía TODAS las tarjetas de todos los usuarios (fuga de datos).
        # Ahora se limita a las del usuario autenticado. El listado real de
        # tarjetas ahora vive en Paymentez (GET /solicitante/pagos/tarjetas/).
        tarjetas = services.list_tarjetas_por_usuario(request.user.username)
        return Response(TarjetaSerializer(tarjetas, many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_tarjeta(request.data))


class TarjetaUserSolicitanteView(SolicitanteAPIView):
    """El GET (por username) es multi-rol, confirmado también en
    Provedor2022 (lectura) — ver TarjetaUserProveedorView. El DELETE (por id
    de tarjeta) está confirmado exclusivo de Solicitante2022."""

    def get(self, request, identifier, format=None):
        return Response(TarjetaSerializer(services.list_tarjetas_por_usuario(identifier), many=True).data)

    def delete(self, request, identifier, format=None):
        return Response(services.eliminar_tarjeta(identifier))
