from rest_framework import status
from rest_framework.response import Response

from api.serializers import CuponSerializer, CuponUsoAdminSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import AdminAPIView
from promotions import services


class CuponesAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.list_cupones())
        if page is not None:
            return self.get_paginated_response(CuponSerializer(page, many=True).data)

    def post(self, request, format=None):
        _, data = services.crear_cupon(request.data, request.POST.getlist("categorias"))
        return Response(data)

    def put(self, request, id, format=None):
        # Se pasa el id de la URL para poder editar también el código.
        data = services.actualizar_cupon(request.data, request.POST.getlist("categorias"), cupon_id=id)
        return Response(data)

    def delete(self, request, id, format=None):
        ok, data = services.eliminar_cupon(id)
        if not ok:
            return Response(data, status=status.HTTP_409_CONFLICT)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CuponDetailsAdminView(AdminAPIView):
    """PUT `cupones/estado/?id=N` (interruptor manual) y GET
    `cupones/<pk>/detalle/` (cupón + estadísticas para la pantalla de detalle
    del admin). El GET plano `cupones/<pk>` lo consume también Solicitante2022 y
    vive en `promotions.api.web.views.CuponDetalleWebView`."""

    def get(self, request, pk, format=None):
        try:
            cupon = services.obtener_cupon(pk)
        except Exception:
            return Response({"error": "No se encontró el cupón."}, status=status.HTTP_404_NOT_FOUND)
        return Response(CuponSerializer(cupon).data)

    def put(self, request, format=None):
        services.actualizar_estado_cupon(request.GET.get("id"), request.data.get("estado"))
        return Response(status=status.HTTP_200_OK)


class CuponUsosAdminView(AdminAPIView, MyPaginationMixin):
    """Paginado: quién canjeó el cupón y si ya lo usó en un pago."""

    pagination_class = MyCustomPagination

    def get(self, request, pk, format=None):
        page = self.paginate_queryset(services.usos_de_cupon(pk))
        if page is not None:
            return self.get_paginated_response(CuponUsoAdminSerializer(page, many=True).data)
        return Response([])
