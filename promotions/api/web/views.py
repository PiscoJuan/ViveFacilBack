from rest_framework.response import Response

from api.serializers import CuponCategoriaSerializer, CuponSerializer, PromocionCategoriaSerializer, PromocionSerializer
from core.permissions import IsAdministrador, IsPublic
from core.views import WebAPIView
from promotions import services


class ConfirmarDescuentoWebView(WebAPIView):
    """Devuelve un string
    plano ("descuento"/"reclamado"/"usado"/"no_existe") — mantener ese
    formato, el frontend lo compara directo, no envolver en un dict."""

    def get(self, request, mail, format=None):
        return Response(services.confirmar_descuento(mail))


class PromocionesWebView(WebAPIView):
    """GET público real (Solicitante2022 y Admin2022); POST admin-exclusivo
    (Admin2022 crea promociones por acá, no por un endpoint namespaced
    separado)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsPublic()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        return Response(PromocionSerializer(services.list_promociones(), many=True).data)

    def post(self, request, format=None):
        _, data = services.crear_promocion(request.data, request.POST.getlist('categorias'))
        return Response(data)


class CuponDetalleWebView(WebAPIView):
    """Confirmado real: Solicitante2022 y Admin2022."""

    def get(self, request, pk, format=None):
        return Response(CuponSerializer(services.obtener_cupon(pk)).data)


class CuponCantidadWebView(WebAPIView):
    """Sin consumidor real confirmado en ningún frontend."""

    def put(self, request, pk, format=None):
        services.actualizar_cantidad_cupon(pk, request.data.get('cantidad'))
        return Response(status=200)


class PromocionesCategoriaWebView(WebAPIView):
    """Sin consumidor real confirmado en ningún frontend."""

    def get(self, request, promCode, format=None):
        return Response(PromocionCategoriaSerializer(services.promociones_por_categoria(promCode), many=True).data)


class AllPromocionesCategoriaWebView(WebAPIView):
    """Sin consumidor real confirmado en ningún frontend."""

    def get(self, request, format=None):
        return Response(PromocionCategoriaSerializer(services.all_promociones_categoria(), many=True).data)


class CuponesCategoriaWebView(WebAPIView):
    """Sin consumidor real confirmado en ningún frontend."""

    def get(self, request, cupCode, format=None):
        return Response(CuponCategoriaSerializer(services.cupones_por_categoria(cupCode), many=True).data)
