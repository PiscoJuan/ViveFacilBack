import logging

from rest_framework.response import Response

from api.serializers import SolicitudEnProcesoSerializer, SolicitudSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import SolicitanteAPIView
from solicitudes import services

logger = logging.getLogger(__name__)


def _listado_response(queryset):
    """Shape común a las 4 variantes no paginadas (pendientes/pasadas/pagadas/no pagadas)."""
    try:
        serializer = SolicitudSerializer(queryset, many=True)
        return Response({"success": True, "num_solicitudes": len(queryset), "solicitudes": serializer.data})
    except Exception as e:
        return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes: " + str(e)})


class SolicitudesPendientesSolicitanteView(SolicitanteAPIView):
    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_pendientes_queryset(correo))


class SolicitudesPendientesPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(services.solicitudes_pendientes_queryset(correo))
            if page is not None:
                return self.get_paginated_response(SolicitudSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes en espera: " + str(e)})


class SolicitudesPasadasSolicitanteView(SolicitanteAPIView):
    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_pasadas_queryset(correo))


class SolicitudesPasadasPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """A diferencia de sus hermanas, no recibe `correo` por URL: filtra por `request.user`."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        try:
            ordenar = request.GET.get("ordenar", None)
            page = self.paginate_queryset(services.solicitudes_pasadas_pag_queryset(request.user, ordenar))
            if page is not None:
                return self.get_paginated_response(SolicitudSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pasadas: " + str(e)})


class SolicitudesPagadasSolicitanteView(SolicitanteAPIView):
    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_pagadas_queryset(correo))


class SolicitudesPagadasPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(services.solicitudes_pagadas_queryset(correo))
            if page is not None:
                return self.get_paginated_response(SolicitudSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pagadas: " + str(e)})


class SolicitudesNoPagadasSolicitanteView(SolicitanteAPIView):
    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_no_pagadas_queryset(correo))


class SolicitudesNoPagadasPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(services.solicitudes_no_pagadas_queryset(correo))
            if page is not None:
                return self.get_paginated_response(SolicitudSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes no pagadas: " + str(e)})


class SolicitudesEnProcesoSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        try:
            ordenar = request.GET.get("ordenar", None)
            page = self.paginate_queryset(services.solicitudes_en_proceso_queryset(request.user, ordenar))
            if page is not None:
                return self.get_paginated_response(SolicitudEnProcesoSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pasadas: " + str(e)})


class AddSolicitudSolicitanteView(SolicitanteAPIView):
    def post(self, request, format=None):
        solicitud, data = services.crear_solicitud(request.data, request.FILES)
        if solicitud is not None:
            try:
                data["solicitud"] = SolicitudSerializer(solicitud).data
            except Exception as e:
                logger.error(
                    "Solicitud se creó OK pero falló al serializarla para la respuesta",
                    extra={"solicitud_id": solicitud.id},
                    exc_info=True,
                )
                data["message"] = "La solicitud se creó pero no se pudo armar la respuesta: " + str(e)
        return Response(data)


class AdjudicarSolicitudSolicitanteView(SolicitanteAPIView):
    def put(self, request, solicitud_ID, format=None):
        _, data = services.adjudicar_solicitud(solicitud_ID, request.data.get("proveedor"), request.data)
        return Response(data)


class EnvioInteresadosSolicitanteView(SolicitanteAPIView):
    def get(self, request, solicitud_ID, format=None):
        return Response(services.envio_interesados(solicitud_ID))


class SolicitudDetalleSolicitanteView(SolicitanteAPIView):
    """Misma lectura que `SolicitudDetalleProveedorView` pero bajo permiso
    `IsSolicitante` — Solicitante2022 llama la misma ruta legacy que
    Provedor2022, cada uno con su propio rol."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.obtener_solicitud_por_id(solicitud_ID))


class SolicitudAdjudicadaSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con proveedor (ver `SolicitudAdjudicadaProveedorView`)."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.solicitud_adjudicada(solicitud_ID))


class HistorialSolicitudesSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con proveedor (ver `HistorialSolicitudesProveedorView`)."""

    def get(self, request, user, format=None):
        return Response(services.historial_solicitudes_por_email(user))


class SolicitudSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con proveedor (ver `SolicitudProveedorView`)."""

    def get(self, request, format=None):
        return Response(services.listar_todas_solicitudes())

    def put(self, request, solicitud_ID, format=None):
        data, http_status = services.actualizar_solicitud(solicitud_ID, request.data)
        return Response(data, status=http_status)
