from rest_framework.response import Response

from api.serializers import SolicitudSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import ProveedorAPIView
from solicitudes import services


class SolicitudPorServicioProveedorView(ProveedorAPIView):
    def get(self, request, ID_servicio, format=None):
        solicitudes = services.solicitud_por_servicio_pendientes(request.user, ID_servicio)
        return Response(SolicitudSerializer(solicitudes, many=True).data)


class SolicitudDetalleProveedorView(ProveedorAPIView):
    """Solo lectura de una solicitud puntual — no confundir con cancelar,
    que es un PUT a `SolicitudProveedorView` (`putCancelarSolicitud`)."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.obtener_solicitud_por_id(solicitud_ID))


class EnvioProveedorView(ProveedorAPIView):
    def get(self, request, solicitud_ID, format=None):
        return Response(services.envio_interesado_lectura(solicitud_ID))

    def put(self, request, solicitud_ID, format=None):
        data, http_status = services.actualizar_envio_interesado(
            solicitud_ID, request.user.username, request.data)
        return Response(data, status=http_status)

    def delete(self, request, solicitud_ID, format=None):
        return Response(services.eliminar_envio_interesado(solicitud_ID, request.user.username))


class InteresadosProveedorView(ProveedorAPIView):
    """Variante sin paginar de InteresadosPagProveedorView (misma query)."""

    def get(self, request, id_proveedor_user_datos, format=None):
        from api.serializers import Envio_InteresadosSerializer
        qs = services.interesados_pag_queryset(id_proveedor_user_datos)
        return Response(Envio_InteresadosSerializer(qs, many=True).data)


class InteresadosPagProveedorView(ProveedorAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        try:
            page = self.paginate_queryset(services.interesados_pag_queryset(id_proveedor_user_datos))
            if page is not None:
                from api.serializers import Envio_InteresadosSerializer
                return self.get_paginated_response(Envio_InteresadosSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pasadas: " + str(e)})


class InteresadosEnProcesoPagProveedorView(ProveedorAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        from api.serializers import Envio_InteresadosSerializer
        try:
            ordenar = request.GET.get("ordenar", None)
            qs = services.interesados_en_proceso_pag_queryset(id_proveedor_user_datos, ordenar)
            page = self.paginate_queryset(qs)
            if page is not None:
                return self.get_paginated_response(Envio_InteresadosSerializer(page, many=True).data)
            return Response(Envio_InteresadosSerializer(qs, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes en proceso: " + str(e)})


class InteresadosPasadasPagProveedorView(ProveedorAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        from api.serializers import Envio_InteresadosSerializer
        try:
            ordenar = request.GET.get("ordenar", None)
            qs = services.interesados_pasadas_pag_queryset(id_proveedor_user_datos, ordenar)
            page = self.paginate_queryset(qs)
            if page is not None:
                return self.get_paginated_response(Envio_InteresadosSerializer(page, many=True).data)
            return Response(Envio_InteresadosSerializer(qs, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pasadas: " + str(e)})


class SolicitudProveedorView(ProveedorAPIView):
    """Endpoint compartido con solicitante (ver `SolicitudSolicitanteView`).
    `putCancelarSolicitud`/`putFinalizarSolicitud` en Provedor2022 hacen PUT
    acá con distinto `termino` en el body."""

    def get(self, request, format=None):
        return Response(services.listar_todas_solicitudes())

    def put(self, request, solicitud_ID, format=None):
        data, http_status = services.actualizar_solicitud(solicitud_ID, request.data)
        return Response(data, status=http_status)


class InteresadosPagEfectivoProveedorView(ProveedorAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        try:
            page = self.paginate_queryset(services.interesados_pag_efectivo_queryset(id_proveedor_user_datos))
            if page is not None:
                from api.serializers import Envio_InteresadosSerializer
                return self.get_paginated_response(Envio_InteresadosSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pasadas: " + str(e)})


class InteresadosPagTarjetaProveedorView(ProveedorAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, id_proveedor_user_datos, format=None):
        try:
            page = self.paginate_queryset(services.interesados_pag_tarjeta_queryset(id_proveedor_user_datos))
            if page is not None:
                from api.serializers import Envio_InteresadosSerializer
                return self.get_paginated_response(Envio_InteresadosSerializer(page, many=True).data)
        except Exception as e:
            return Response({"success": False, "message": "No se pudo obtener la lista de solicitudes pasadas: " + str(e)})


class SolicitudesPagadasProveedorView(ProveedorAPIView):
    def get(self, request, id, format=None):
        return Response(services.solicitudes_pagadas_por_proveedor(id))


class InteresadosPorFechaProveedorView(ProveedorAPIView):
    def post(self, request, id_proveedor_user_datos, format=None):
        data = services.interesados_por_fecha(
            id_proveedor_user_datos, request.data.get("dateInicio"), request.data.get("dateFinal")
        )
        return Response(data)


class SolicitudAdjudicadaProveedorView(ProveedorAPIView):
    """Endpoint compartido con solicitante (ver `SolicitudAdjudicadaSolicitanteView`)."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.solicitud_adjudicada(solicitud_ID))


class HistorialSolicitudesProveedorView(ProveedorAPIView):
    """Endpoint compartido con solicitante (ver `HistorialSolicitudesSolicitanteView`)."""

    def get(self, request, user, format=None):
        return Response(services.historial_solicitudes_por_email(user))


class AddSolicitudProveedorView(ProveedorAPIView):
    """Endpoint compartido con solicitante (ver `AddSolicitudSolicitanteView`)."""

    def post(self, request, format=None):
        solicitud, data = services.crear_solicitud(request.data, request.FILES)
        if solicitud is not None:
            data["solicitud"] = SolicitudSerializer(solicitud).data
        return Response(data)
