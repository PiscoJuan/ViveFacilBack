import datetime

from rest_framework import status
from rest_framework.response import Response

from api.serializers import (
    PagoEfectivoSerializer, PagoSolicitudSerializer, PagoTarjetaSerializer,
    PlanProveedorSerializer, PlanSerializer, ProveedorSerializer,
)
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import AdminAPIView
from payments import services


class PlanesAdminView(AdminAPIView):
    """Réplica de Planes (api/views.py:4315), CRUD completo, admin-
    exclusivo (grep confirmado en los 4 frontends)."""

    def get(self, request, format=None):
        return Response(PlanSerializer(services.list_planes(), many=True).data)

    def post(self, request, format=None):
        data, valido = services.crear_plan(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_201_CREATED)

    def put(self, request, format=None):
        data, valido = services.actualizar_plan(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        return Response(services.eliminar_plan(id))


class PlanesEstadoAdminView(AdminAPIView):
    """Réplica de PlanesEstado (api/views.py:4513)."""

    def get(self, request, format=None):
        return Response(PlanSerializer(services.list_planes_activos(), many=True).data)


class PlanProveedorAdminView(AdminAPIView):
    """Réplica de PlanProveedorView (api/views.py:4480), CRUD completo."""

    def get(self, request, format=None):
        return Response(PlanProveedorSerializer(services.list_planes_proveedor(), many=True).data)

    def post(self, request, format=None):
        data, valido = services.crear_plan_proveedor(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_201_CREATED)

    def put(self, request, format=None):
        data, valido = services.actualizar_plan_proveedor(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_200_OK)

    def delete(self, request, id, format=None):
        return Response(services.eliminar_plan_proveedor(id))


class PagosEfectivoAdminView(AdminAPIView):
    """Réplica de PagosEfectivoUser.get (api/views.py), Fase 5 Bloque 3."""

    def get(self, request, format=None):
        return Response(PagoEfectivoSerializer(services.list_pagos_efectivo(), many=True).data)


class PagosEfectivoPaginadoAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de PagosEfectivoUserP.get (api/views.py), Fase 5 Bloque 3."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.list_pagos_efectivo().order_by('-id'))
        if page is not None:
            return self.get_paginated_response(PagoEfectivoSerializer(page, many=True).data)


class PagosTarjetaAdminView(AdminAPIView):
    """Réplica de PagosTarjetaUser (api/views.py), Fase 5 Bloque 3. Sirve
    los alias de URL legacy `pago_tarjetas/` (GET) y `tarjeta_pago/` (PUT) —
    confirmado por grep que cada frontend usa un alias distinto para un
    verbo distinto de la misma vista."""

    def get(self, request, format=None):
        return Response(PagoTarjetaSerializer(services.list_pagos_tarjeta(), many=True).data)

    def put(self, request, format=None):
        services.actualizar_pago_tarjeta(request.GET.get('id'), request.data.get('estado'))
        return Response(status=status.HTTP_200_OK)


class PagosTarjetaPaginadoAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de PagosTarjetaUserP.get (api/views.py), Fase 5 Bloque 3."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.list_pagos_tarjeta().order_by('-id'))
        if page is not None:
            return self.get_paginated_response(PagoTarjetaSerializer(page, many=True).data)


class PagosEfectivoFechasAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de EfectivosFilter.get (api/views.py), Fase 5 Bloque 3."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        fecha_inicio = datetime.datetime.strptime(request.GET.get("fechaInicio"), "%Y-%m-%d")
        fecha_fin = datetime.datetime.strptime(request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(services.filtrar_pagos_efectivo_por_fecha(fecha_inicio, fecha_fin))
        if page is not None:
            return self.get_paginated_response(PagoEfectivoSerializer(page, many=True).data)


class PagosTarjetaFechasAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de TarjetasFilter.get (api/views.py), Fase 5 Bloque 3."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        fecha_inicio = datetime.datetime.strptime(request.GET.get("fechaInicio"), "%Y-%m-%d")
        fecha_fin = datetime.datetime.strptime(request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(services.filtrar_pagos_tarjeta_por_fecha(fecha_inicio, fecha_fin))
        if page is not None:
            return self.get_paginated_response(PagoTarjetaSerializer(page, many=True).data)


class ValorTotalEfectivoAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(services.valor_total_efectivo())


class ValorTotalTarjetaAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(services.valor_total_tarjeta())


class ValorTotalPayTarjetaAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(services.valor_total_pay_tarjeta())


class ValorTotalBancTarjetaAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(services.valor_total_banc_tarjeta())


class ValorTotalSisTarjetaAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(services.valor_total_sis_tarjeta())


class ValorTotalAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(services.valor_total())


class ValorTotalProveedoresAdminView(AdminAPIView):
    """Réplica de ValorTotalProveedores.get (api/views.py), Fase 5 Bloque 3."""

    def get(self, request, format=None):
        return Response(services.valor_total_proveedores())


class PagosSolicitudEfectivoAdminView(AdminAPIView):
    def get(self, request, pago_ID, format=None):
        return Response(PagoSolicitudSerializer(services.list_pagos_solicitud_efectivo(pago_ID), many=True).data)


class PagosSolicitudTarjetaAdminView(AdminAPIView):
    def get(self, request, pago_ID, format=None):
        return Response(PagoSolicitudSerializer(services.list_pagos_solicitud_tarjeta(pago_ID), many=True).data)


class PlanProveedoresFiltroFechaAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de PlanProveedores_Filter_Date (api/views.py:1100), cleanup
    post-Fase-5 Bloque 3. Sin evidencia de llamador real en ningún
    frontend — se migra igual por consistencia."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(
            services.proveedores_por_fecha_plan(request.GET.get("fechaInicio"), request.GET.get("fechaFin"))
        )
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)


class ProveedoresFiltroFechaYNombreAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de ProveedoresDate_Search_Name (api/views.py:1949), cleanup
    post-Fase-5 Bloque 3. Sin evidencia de llamador real en ningún
    frontend — se migra igual por consistencia."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(
            services.proveedores_por_fecha_y_nombre(
                request.GET.get("fechaInicio"), request.GET.get("fechaFin"), request.GET.get("user")
            )
        )
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)
