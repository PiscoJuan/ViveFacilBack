from rest_framework.response import Response

from api.serializers import SolicitudSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import ProveedorAPIView
from solicitudes import services


class SolicitudPorServicioProveedorView(ProveedorAPIView):
    """Réplica de Solicitud_Servicio_User (api/views.py:3013)."""

    def get(self, request, ID_servicio, format=None):
        solicitudes = services.solicitud_por_servicio_pendientes(request.user, ID_servicio)
        return Response(SolicitudSerializer(solicitudes, many=True).data)


class SolicitudDetalleProveedorView(ProveedorAPIView):
    """Réplica de SolicitudID (api/views.py:1669). El doc de fase proponía
    el nombre `.../cancelar/` para este path, pero el frontend real
    (`getSolicitudById`/`getSolicitudByIDs` en python-anywhere.service.ts)
    solo lo usa para leer una solicitud puntual — la acción de cancelar de
    verdad pasa por `PUT solicitud/<id>` (`putCancelarSolicitud`), que es
    `SolicitudProveedorView` de abajo. Se registra como `.../detalle/` para
    reflejar lo que la vista realmente hace, no lo que su nombre sugiere."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.obtener_solicitud_por_id(solicitud_ID))


class EnvioProveedorView(ProveedorAPIView):
    """Réplica de Envio (api/views.py:3026). Antes tenía permission_classes
    = [IsAuthenticated] (cualquier usuario logueado, no solo proveedor);
    la ruta nueva exige IsProveedor estructuralmente."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.envio_interesado_lectura(solicitud_ID))

    def put(self, request, solicitud_ID, format=None):
        data, http_status = services.actualizar_envio_interesado(
            solicitud_ID, request.user.username, request.data)
        return Response(data, status=http_status)

    def delete(self, request, solicitud_ID, format=None):
        return Response(services.eliminar_envio_interesado(solicitud_ID, request.user.username))


class InteresadosPagProveedorView(ProveedorAPIView, MyPaginationMixin):
    """Réplica de Proveedores_Interesados_Pag (api/views.py:3240). Antes sin
    ningún permission_classes (abierto); la ruta nueva exige IsProveedor."""

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
    """Réplica de Proveedores_Interesados_Proceso_Pag (api/views.py:3260)."""

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
    """Réplica de Proveedores_Interesados_Pasadas_Pag (api/views.py:3292)."""

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
    """Réplica de Solicituds (api/views.py:2131), endpoint multi-rol
    compartido con solicitante (ver SolicitudSolicitanteView en
    solicitudes/api/solicitante/views.py, Fase 3). La ruta legacy
    `solicitud/`/`solicitud/<id>` sigue sirviendo ambos roles sin cambio de
    permiso — se conserva hasta confirmar tráfico cero. Usada por
    `putCancelarSolicitud`/`putFinalizarSolicitud` en Provedor2022, ambas
    hacen PUT a `solicitud/<id>` con distinto `termino` en el body."""

    def get(self, request, format=None):
        return Response(services.listar_todas_solicitudes())

    def put(self, request, solicitud_ID, format=None):
        data, http_status = services.actualizar_solicitud(solicitud_ID, request.data)
        return Response(data, status=http_status)


class InteresadosPagEfectivoProveedorView(ProveedorAPIView, MyPaginationMixin):
    """Réplica de Proveedores_Interesados_Efectivo_Pag (api/views.py:1464),
    cleanup post-Fase-5 Bloque 3. El checklist original decía "probable
    admin/reportería" — grep fresco confirmó uso real exclusivo de
    Provedor2022 (`historial.page.ts`), corregido acá."""

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
    """Réplica de Proveedores_Interesados_Tarjeta_Pag (api/views.py:1484),
    cleanup post-Fase-5 Bloque 3. Mismo caso que
    InteresadosPagEfectivoProveedorView — confirmado exclusivo Provedor2022."""

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
    """Réplica de SolicitudesPagadas (api/views.py:1470), cleanup post-Fase-5
    Bloque 3. Sin evidencia de llamador real en ningún frontend — se migra
    igual por consistencia."""

    def get(self, request, id, format=None):
        return Response(services.solicitudes_pagadas_por_proveedor(id))


class InteresadosPorFechaProveedorView(ProveedorAPIView):
    """Réplica de Proveedores_InteresadosFecha (api/views.py:1453), cleanup
    post-Fase-5 Bloque 3. El comentario legacy decía "Quitar, ya no se va a
    usar" pero está confirmado en uso activo por Provedor2022 (grep fresco:
    `python-anywhere.service.ts:143`) — no se borra."""

    def post(self, request, id_proveedor_user_datos, format=None):
        data = services.interesados_por_fecha(
            id_proveedor_user_datos, request.data.get("dateInicio"), request.data.get("dateFinal")
        )
        return Response(data)


class SolicitudAdjudicadaProveedorView(ProveedorAPIView):
    """Réplica de SolicitudAdjudicada (api/views.py:750), endpoint multi-rol
    (cleanup post-Fase-5, Bloque 3)."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.solicitud_adjudicada(solicitud_ID))


class HistorialSolicitudesProveedorView(ProveedorAPIView):
    """Réplica de Solicitudes (api/views.py:801), endpoint multi-rol
    confirmado por grep fresco: Provedor2022 y Solicitante2022 lo llaman
    igual (cleanup post-Fase-5, Bloque 3)."""

    def get(self, request, user, format=None):
        return Response(services.historial_solicitudes_por_email(user))


class AddSolicitudProveedorView(ProveedorAPIView):
    """Réplica de AddSolicitud (api/views.py:2200), endpoint multi-rol
    (ver AddSolicitudSolicitanteView, Fase 3, para el detalle de cómo se
    descubrió que Provedor2022 también lo llama)."""

    def post(self, request, format=None):
        solicitud, data = services.crear_solicitud(request.data, request.FILES)
        if solicitud is not None:
            data["solicitud"] = SolicitudSerializer(solicitud).data
        return Response(data)
