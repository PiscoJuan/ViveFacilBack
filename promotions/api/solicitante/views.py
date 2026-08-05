from rest_framework.response import Response

from api.serializers import Cupon_AplicadoSerializer, CuponCategoriaSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import SolicitanteAPIView
from promotions import services


class CuponAplicadoSolicitanteView(SolicitanteAPIView):
    def get(self, request, user, format=None):
        serializer = Cupon_AplicadoSerializer(
            services.cupones_aplicados_activos(user), many=True
        )
        return Response(serializer.data)


class CuponAplicadoPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """Igual que CuponAplicadoSolicitanteView pero paginada, para el scroll
    infinito de "Mis cupones" en Solicitante2022."""

    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        page = self.paginate_queryset(services.cupones_aplicados_activos(user))
        return self.get_paginated_response(Cupon_AplicadoSerializer(page, many=True).data)


class CuponCategoriaSolicitanteView(SolicitanteAPIView):
    def get(self, request, format=None):
        serializer = CuponCategoriaSerializer(
            services.cupones_categoria_disponibles(request.user.username), many=True
        )
        return Response(serializer.data)


class CuponCategoriaPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """Igual que CuponCategoriaSolicitanteView pero paginada, para el scroll
    infinito de "Canjear cupones" en Solicitante2022."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.cupones_categoria_disponibles(request.user.username))
        return self.get_paginated_response(CuponCategoriaSerializer(page, many=True).data)


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
