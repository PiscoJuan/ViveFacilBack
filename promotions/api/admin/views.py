from rest_framework import status
from rest_framework.response import Response

from api.serializers import CuponSerializer, PromocionSerializer
from core.views import AdminAPIView
from promotions import services


class PromocionesListAdminView(AdminAPIView):
    """Ruta base `admin/promotions/promociones/` (GET+POST) — antes
    Admin2022 la pedía en `web/promotions/promociones/` (misma lógica que
    promotions.api.web.views.PromocionesWebView)."""

    def get(self, request, format=None):
        return Response(PromocionSerializer(services.list_promociones(), many=True).data)

    def post(self, request, format=None):
        _, data = services.crear_promocion(request.data, request.POST.getlist('categorias'))
        return Response(data)


class PromocionesAdminView(AdminAPIView):
    """Solo PUT (`promocion_update/<id>`)/DELETE (`promocion_delete/<id>`),
    admin-exclusivas. El GET (`promociones/`, compartido de verdad con
    Solicitante2022) y el POST viven en
    `promotions.api.web.views.PromocionesWebView`, con permiso endurecido
    a IsAdministrador para todo lo que no sea GET."""

    def put(self, request, id, format=None):
        data = services.actualizar_promocion(request.data, request.POST.getlist("categorias"))
        return Response(data)

    def delete(self, request, id, format=None):
        services.eliminar_promocion(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PromocionDetailsAdminView(AdminAPIView):
    def get(self, request, pk, format=None):
        return Response(PromocionSerializer(services.obtener_promocion(pk)).data)

    def put(self, request, format=None):
        services.actualizar_estado_promocion(request.GET.get("id"), request.data.get("estado"))
        return Response(status=status.HTTP_200_OK)


class CuponesAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(CuponSerializer(services.list_cupones(), many=True).data)

    def post(self, request, format=None):
        _, data = services.crear_cupon(request.data, request.POST.getlist("categorias"))
        return Response(data)

    def put(self, request, id, format=None):
        data = services.actualizar_cupon(request.data, request.POST.getlist("categorias"))
        return Response(data)

    def delete(self, request, id, format=None):
        services.eliminar_cupon(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CuponDetailsAdminView(AdminAPIView):
    """Solo PUT (`cupon_estado/`), admin-exclusivo. El GET (`cupones/<pk>`)
    lo consume también Solicitante2022 y vive en
    `promotions.api.web.views.CuponDetalleWebView`."""

    def put(self, request, format=None):
        services.actualizar_estado_cupon(request.GET.get("id"), request.data.get("estado"))
        return Response(status=status.HTTP_200_OK)
