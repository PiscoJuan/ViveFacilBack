import datetime

from rest_framework import status
from rest_framework.response import Response

from api.serializers import Profesion_ProveedorSerializer
from catalog import services
from catalog.api.admin.serializers import CategoriaSerializer, SolicitudProfesionSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import AdminAPIView


class CategoriasAdminView(AdminAPIView):
    """Réplica de Categorias (api/views.py:716), Fase 5. Solo gestión
    (POST/PUT/DELETE) — el GET no tiene evidencia de consumidor fuera del
    panel admin (a diferencia de Servicios/Profesiones, cuyo GET ya es
    público desde la Fase 2), así que se migra completo."""

    def get(self, request, format=None):
        return Response(CategoriaSerializer(services.listar_categorias(), many=True).data)

    def post(self, request, format=None):
        categoria, data = services.crear_categoria(
            request.POST.get("nombre"), request.POST.get("descripcion"), request.FILES.get("foto")
        )
        if categoria is None:
            data["error"] = data.get("error", "Error al crear!.")
        return Response(data)

    def put(self, request, id, format=None):
        data, valido = services.actualizar_categoria(id, request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        services.eliminar_categoria(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiciosAdminView(AdminAPIView):
    """Réplica del PUT/DELETE de Servicios en `servicios/<id>`
    (api/views.py:818), ambos ya admin-exclusivos en esa URL (grep
    confirmado). El GET (`web/catalog/servicios/`, Fase 2) y el POST
    (comparte URL `servicios/` con el GET) NO se tocan acá: `Servicios.post`
    en api/views.py delega a `catalog.services.crear_servicio`, con
    `get_permissions()` endurecido a IsAdministrador para todo lo que no
    sea GET (antes exigía solo IsAuthenticated — cualquier usuario logueado,
    de cualquier rol, podía crear/editar/borrar servicios)."""

    def put(self, request, id, format=None):
        data, valido = services.actualizar_servicio(id, request.data.copy())
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        services.desactivar_servicio(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfesionesAdminView(AdminAPIView):
    """Réplica del DELETE de Profesiones en `profesiones/<pk>`
    (api/views.py:1714), la única URL admin-exclusiva propia de esta clase.
    El GET (`web/catalog/profesiones/`, Fase 2) y el POST/PUT (comparten la
    URL `profesiones/` con el GET) se quedan en la clase legacy, que ahora
    delega a `catalog.services.crear_profesion`/`actualizar_profesion` con
    el mismo endurecimiento de permiso que Servicios."""

    def delete(self, request, pk, format=None):
        services.eliminar_profesion(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CiudadesAdminView(AdminAPIView):
    """Réplica del POST de Ciudades (api/views.py:4456), registrada acá
    además de en la ruta legacy `ciudades/` (que comparte URL con el GET,
    compartido de verdad por Proveedor2022 y Solicitante2022 — grep
    confirmado, no se toca). El PUT que llama Admin2022 a `ciudades/` no
    existe en ningún lado del backend (`Ciudades` nunca definió ese método,
    ver docs/refactor/CHECKLIST-inventario-endpoints.md) — no se inventa
    acá, es una decisión de producto pendiente."""

    def post(self, request, format=None):
        data, valido = services.crear_ciudad(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_201_CREATED)


class SolicitudesProfesionAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de SolicitudProfesionProveedor (api/views.py:1413), Fase 5."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.listar_solicitudes_profesion())
        if page is not None:
            return self.get_paginated_response(SolicitudProfesionSerializer(page, many=True).data)


class SolicitudPorUsuarioAdminView(AdminAPIView):
    """Réplica de SolicitudByName (api/views.py:1509). Sin evidencia de uso
    real en ningún frontend (grep confirmado sobre
    `solicitudes-proveedores/<user>`) — se migra igual por consistencia de
    namespace."""

    def get(self, request, user, format=None):
        return Response(SolicitudProfesionSerializer(services.solicitudes_profesion_por_usuario(user), many=True).data)


class SolicitudProfesionDetalleAdminView(AdminAPIView):
    """Réplica de SolicitudDetails (api/views.py:1519)."""

    def get(self, request, pk, format=None):
        return Response(SolicitudProfesionSerializer(services.obtener_solicitud_profesion(pk)).data)


class ManejoSolicitudAdminView(AdminAPIView):
    """Réplica de ManejoSolicitud (api/views.py:1426-1472), Fase 5. Atendía 3
    paths viejos con verbos distintos: GET/POST
    (`obtener_solicitudes_profesiones/`, `crear_solicitud_profesion/`) no
    tienen evidencia de consumidor en ninguno de los 4 frontends (grep
    fresco confirmado); PUT/DELETE (`change-solicitud/<pk>`) sí los usa
    Admin2022 activamente. Se migra la clase completa sin split: a
    diferencia de otros casos de esta fase donde el split por verbo sí se
    confirmó con grep (ej. `SendNotificacion` en el Bloque 3), acá no hay
    evidencia de que GET/POST pertenezcan a otro rol — son código sin
    consumidor conocido, no un flujo real de otro rol."""

    def get(self, request, format=None):
        return Response(SolicitudProfesionSerializer(services.obtener_solicitudes_profesion(), many=True).data)

    def post(self, request, format=None):
        data, solicitud = services.crear_solicitud_profesion(
            request.data.get("proveedor"), request.data.get("profesion"),
            request.data.get("anio"), request.FILES.get("documento"),
        )
        if solicitud is not None:
            return Response(SolicitudProfesionSerializer(solicitud).data)
        return Response(data)

    def put(self, request, pk, format=None):
        solicitud = services.actualizar_solicitud_profesion(pk, request.data.get("estado"))
        return Response(SolicitudProfesionSerializer(solicitud).data)

    def delete(self, request, pk, format=None):
        services.eliminar_solicitud_profesion(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CrearProfesionesFaltantesAdminView(AdminAPIView):
    """Réplica de CrearProfesionesFaltantesView (api/views.py:853), cleanup
    post-Fase-5, Bloque 4. Sin evidencia de consumidor real en ningún
    frontend (grep fresco, cero resultados) — se migra igual por
    consistencia."""

    def post(self, request, format=None):
        return Response(services.crear_profesiones_faltantes())


class ProfesionProveedorAdminView(AdminAPIView):
    """Réplica de ProfesionProveedor (api/views.py:903), cleanup
    post-Fase-5, Bloque 4. Sin consumidor real confirmado (ver
    `catalog.services.profesiones_por_proveedor`)."""

    def get(self, request, proveedor_id, format=None):
        return Response(Profesion_ProveedorSerializer(services.profesiones_por_proveedor(proveedor_id), many=True).data)


class SincronizarProfesionProveedorAdminView(AdminAPIView):
    """Réplica de SincronizarProfesionProveedorView (api/views.py:740),
    cleanup post-Fase-5, Bloque 4. Sin evidencia de consumidor real en
    ningún frontend."""

    def post(self, request, format=None):
        return Response(services.sincronizar_profesion_proveedor())


class SolicitudesProfesionBusquedaAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Solicitudes_Search_Name (api/views.py:1528)."""

    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        page = self.paginate_queryset(services.buscar_solicitudes_profesion_por_nombre(user))
        if page is not None:
            return self.get_paginated_response(SolicitudProfesionSerializer(page, many=True).data)


class SolicitudesProfesionFechaAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Solicitudes_Filter_Date (api/views.py:1543)."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        fecha_inicio = datetime.datetime.strptime(request.GET.get("fechaInicio"), "%Y-%m-%d")
        fecha_fin = datetime.datetime.strptime(request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(services.filtrar_solicitudes_profesion_por_fecha(fecha_inicio, fecha_fin))
        if page is not None:
            return self.get_paginated_response(SolicitudProfesionSerializer(page, many=True).data)
