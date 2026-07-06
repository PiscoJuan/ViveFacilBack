from rest_framework.response import Response

from api.serializers import SolicitudEnProcesoSerializer, SolicitudSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import SolicitanteAPIView
from solicitudes import services


def _listado_response(queryset):
    """Réplica del shape {'success','num_solicitudes','solicitudes'} común
    a las 4 variantes no paginadas (SolicitudesPending/Past/Paid/NoPaid)."""
    try:
        serializer = SolicitudSerializer(queryset, many=True)
        return Response({"success": True, "num_solicitudes": len(queryset), "solicitudes": serializer.data})
    except Exception as e:
        return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes: " + str(e)})


class SolicitudesPendientesSolicitanteView(SolicitanteAPIView):
    """Réplica de SolicitudesPending (api/views.py:1923)."""

    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_pendientes_queryset(correo))


class SolicitudesPendientesPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """Réplica de SolicitudesPendingPag (api/views.py:1903)."""

    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(services.solicitudes_pendientes_queryset(correo))
            if page is not None:
                return self.get_paginated_response(SolicitudSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes en espera: " + str(e)})


class SolicitudesPasadasSolicitanteView(SolicitanteAPIView):
    """Réplica de SolicitudesPast (api/views.py:2030)."""

    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_pasadas_queryset(correo))


class SolicitudesPasadasPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """Réplica de SolicitudesPastPag (api/views.py:1946) — sin `correo`,
    filtra por `request.user`."""

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
    """Réplica de SolicitudesPaid (api/views.py:2071)."""

    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_pagadas_queryset(correo))


class SolicitudesPagadasPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """Réplica de SolicitudesPaidPag (api/views.py:2051)."""

    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(services.solicitudes_pagadas_queryset(correo))
            if page is not None:
                return self.get_paginated_response(SolicitudSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pagadas: " + str(e)})


class SolicitudesNoPagadasSolicitanteView(SolicitanteAPIView):
    """Réplica de SolicitudesNoPaid (api/views.py:2112)."""

    def get(self, request, correo, format=None):
        return _listado_response(services.solicitudes_no_pagadas_queryset(correo))


class SolicitudesNoPagadasPagSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """Réplica de SolicitudesNoPaidPag (api/views.py:2092)."""

    pagination_class = MyCustomPagination

    def get(self, request, correo, format=None):
        try:
            page = self.paginate_queryset(services.solicitudes_no_pagadas_queryset(correo))
            if page is not None:
                return self.get_paginated_response(SolicitudSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes no pagadas: " + str(e)})


class SolicitudesEnProcesoSolicitanteView(SolicitanteAPIView, MyPaginationMixin):
    """Réplica de SolicitudesEnProceso (api/views.py:1974)."""

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
    """Réplica de AddSolicitud (api/views.py:2200). NOTA: se descubrió por
    grep que `ViveFacil_Provedor2022` también llama `addsolicitud/`
    (`postAddSolicitud`, python-anywhere.service.ts:293 vía `solicitudURL`)
    pese a que el doc de fase lo tageaba como solo-solicitante — es multi-rol
    en la práctica. La ruta legacy sigue sirviendo a ambos sin cambio de
    permiso; esta vista nueva se registra solo bajo `solicitante/` por ahora,
    la de `proveedor/` se agrega en la Fase 4."""

    def post(self, request, format=None):
        solicitud, data = services.crear_solicitud(request.data, request.FILES)
        if solicitud is not None:
            data["solicitud"] = SolicitudSerializer(solicitud).data
        return Response(data)


class AdjudicarSolicitudSolicitanteView(SolicitanteAPIView):
    """Réplica de AdjudicarSolicitud (api/views.py:1846)."""

    def put(self, request, solicitud_ID, format=None):
        _, data = services.adjudicar_solicitud(solicitud_ID, request.data.get("proveedor"), request.data)
        return Response(data)


class EnvioInteresadosSolicitanteView(SolicitanteAPIView):
    """Réplica de Envio_Interesado (api/views.py:4054)."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.envio_interesados(solicitud_ID))


class SolicitudDetalleSolicitanteView(SolicitanteAPIView):
    """Réplica de SolicitudID (api/views.py:2070), endpoint multi-rol que la
    Fase 4 migró como si fuera exclusivo de proveedor (`SolicitudDetalleProveedorView`)
    sin detectar que `ViveFacil_Solicitante2022` también lo llama
    (`getSolicitudById`, legacy `solicitudID/<id>` sin `/detalle/`) — causaba
    403 real para solicitantes. Se agrega esta vista para exponer el mismo
    `services.obtener_solicitud_por_id` bajo permiso IsSolicitante."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.obtener_solicitud_por_id(solicitud_ID))


class SolicitudAdjudicadaSolicitanteView(SolicitanteAPIView):
    """Réplica de SolicitudAdjudicada (api/views.py:750), endpoint multi-rol
    (cleanup post-Fase-5, Bloque 3)."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.solicitud_adjudicada(solicitud_ID))


class HistorialSolicitudesSolicitanteView(SolicitanteAPIView):
    """Réplica de Solicitudes (api/views.py:801), endpoint multi-rol
    confirmado por grep fresco: Solicitante2022 (`getSolicitudesHistorial`)
    y Provedor2022 (ídem) lo llaman igual (cleanup post-Fase-5, Bloque 3)."""

    def get(self, request, user, format=None):
        return Response(services.historial_solicitudes_por_email(user))


class SolicitudSolicitanteView(SolicitanteAPIView):
    """Réplica de Solicituds (api/views.py:2131), endpoint multi-rol
    compartido con proveedor. La ruta legacy `solicitud/`/`solicitud/<id>`
    sigue sirviendo ambos roles sin cambio de permiso hasta la Fase 4."""

    def get(self, request, format=None):
        return Response(services.listar_todas_solicitudes())

    def put(self, request, solicitud_ID, format=None):
        data, http_status = services.actualizar_solicitud(solicitud_ID, request.data)
        return Response(data, status=http_status)
