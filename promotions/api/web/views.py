from rest_framework.response import Response

from api.serializers import CuponCategoriaSerializer, CuponSerializer
from core.views import WebAPIView
from promotions import services


class ConfirmarDescuentoWebView(WebAPIView):
    """Devuelve un string
    plano ("descuento"/"reclamado"/"usado"/"no_existe") — mantener ese
    formato, el frontend lo compara directo, no envolver en un dict."""

    def get(self, request, mail, format=None):
        return Response(services.confirmar_descuento(mail))


class CuponDetalleWebView(WebAPIView):
    """Confirmado real: Solicitante2022 y Admin2022."""

    def get(self, request, pk, format=None):
        return Response(CuponSerializer(services.obtener_cupon(pk)).data)


class CuponCantidadWebView(WebAPIView):
    """Sin consumidor real confirmado en ningún frontend."""

    def put(self, request, pk, format=None):
        services.actualizar_cantidad_cupon(pk, request.data.get('cantidad'))
        return Response(status=200)


class CuponesCategoriaWebView(WebAPIView):
    """Sin consumidor real confirmado en ningún frontend."""

    def get(self, request, cupCode, format=None):
        return Response(CuponCategoriaSerializer(services.cupones_por_categoria(cupCode), many=True).data)
