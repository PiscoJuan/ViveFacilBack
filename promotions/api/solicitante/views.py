from rest_framework.response import Response

from api.serializers import Cupon_AplicadoSerializer, CuponCategoriaSerializer, PromocionSerializer
from core.views import SolicitanteAPIView
from promotions import services


class PromocionesSolicitanteView(SolicitanteAPIView):
    """Endpoint propio del solicitante para listar promociones — antes
    pedía una ruta sin ningún prefijo de rol."""

    def get(self, request, format=None):
        return Response(PromocionSerializer(services.list_promociones(), many=True).data)


class CuponAplicadoSolicitanteView(SolicitanteAPIView):
    def get(self, request, user, format=None):
        serializer = Cupon_AplicadoSerializer(
            services.cupones_aplicados_activos(user), many=True
        )
        return Response(serializer.data)


class CuponCategoriaSolicitanteView(SolicitanteAPIView):
    def get(self, request, format=None):
        serializer = CuponCategoriaSerializer(
            services.cupones_categoria_disponibles(request.user.username), many=True
        )
        return Response(serializer.data)


class RevisarDescuentoUnicoSolicitanteView(SolicitanteAPIView):
    """Devuelve un
    string plano ("descuento"/"no"/"error") — el frontend lo compara
    directo, no envolver en un dict."""

    def get(self, request, format=None):
        return Response(services.revisar_descuento_unico(request.user))


class UsarDescuentoUnicoSolicitanteView(SolicitanteAPIView):
    def get(self, request, mail, format=None):
        return Response(services.usar_descuento_unico(mail))


class CuponAplicadoCrearSolicitanteView(SolicitanteAPIView):
    """Confirmado exclusivo de Solicitante2022 (solo el
    POST tiene consumidor real, ver `promotions.services.actualizar_cupon_aplicado`
    para el bug del PUT)."""

    def post(self, request, format=None):
        return Response(services.crear_cupon_aplicado(
            request.data.get('user'), request.data.get('cupon_id'), request.data.get('estado'),
        ))

    def put(self, request, format=None):
        from rest_framework import status

        ok = services.actualizar_cupon_aplicado(
            request.data.get('user'), request.data.get('cupon_id'), request.data.get('estado'),
        )
        return Response(status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST)
