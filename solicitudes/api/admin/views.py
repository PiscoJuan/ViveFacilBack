from api.serializers import SolicitudAdminSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import AdminAPIView
from solicitudes import services


class SolicitudesAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.todas_solicitudes_admin_queryset(
            estado=request.GET.get("estado"),
            tipo_pago=request.GET.get("tipoPago"),
            servicio=request.GET.get("servicio"),
            texto=request.GET.get("texto"),
            fecha_inicio=request.GET.get("fechaInicio"),
            fecha_fin=request.GET.get("fechaFin"),
        ))
        if page is not None:
            return self.get_paginated_response(SolicitudAdminSerializer(page, many=True).data)
