from rest_framework import status
from rest_framework.response import Response

from api.serializers import CuponSerializer, PromocionSerializer
from core.views import AdminAPIView
from promotions import services


class PromocionesAdminView(AdminAPIView):
    """Réplica del PUT (`promocion_update/<id>`)/DELETE (`promocion_delete/
    <id>`) de Promociones (api/views.py:3639) — únicas URLs propias de esta
    clase, ambas admin-exclusivas. El GET (`promociones/`, compartido de
    verdad con Solicitante2022 — grep confirmado) y el POST (comparte esa
    misma URL con el GET) se quedan en la clase legacy, que ahora delega a
    `promotions.services.crear_promocion` con permiso endurecido a
    IsAdministrador para todo lo que no sea GET."""

    def put(self, request, id, format=None):
        data = services.actualizar_promocion(request.data, request.POST.getlist("categorias"))
        return Response(data)

    def delete(self, request, id, format=None):
        services.eliminar_promocion(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PromocionDetailsAdminView(AdminAPIView):
    """Réplica de Promocion_Details (api/views.py:3776)."""

    def get(self, request, pk, format=None):
        return Response(PromocionSerializer(services.obtener_promocion(pk)).data)

    def put(self, request, format=None):
        services.actualizar_estado_promocion(request.GET.get("id"), request.data.get("estado"))
        return Response(status=status.HTTP_200_OK)


class CuponesAdminView(AdminAPIView):
    """Réplica de Cupones (api/views.py:3792), CRUD completo."""

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
    """Réplica del PUT de Cupon_Details (`cupon_estado/`, api/views.py:3926)
    — único método admin-exclusivo de esa clase. El GET (`cupones/<pk>`) lo
    consume también Solicitante2022 (grep confirmado) — se queda en la
    clase legacy, sin tocar."""

    def put(self, request, format=None):
        services.actualizar_estado_cupon(request.GET.get("id"), request.data.get("estado"))
        return Response(status=status.HTTP_200_OK)
