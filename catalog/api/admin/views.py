import datetime

from rest_framework import status
from rest_framework.response import Response

from api.serializers import Profesion_ProveedorSerializer
from catalog import services
from catalog.api.admin.serializers import (
    CategoriaSerializer,
    ProfesionSerializer,
    ServicioSerializer,
    SolicitudProfesionSerializer,
)
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import AdminAPIView


class CategoriasAdminView(AdminAPIView):
    """El GET es exclusivo de este panel admin, a diferencia de
    Servicios/Profesiones, cuyo GET es público en catalog.api.web.views."""

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
    """Solo PUT/DELETE de `servicios/<id>/`. La ruta base `servicios/`
    (GET+POST) vive en ServiciosListAdminView."""

    def put(self, request, id, format=None):
        data, valido = services.actualizar_servicio(id, request.data.copy())
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        services.desactivar_servicio(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiciosListAdminView(AdminAPIView):
    """Ruta base `admin/catalog/servicios/` (GET+POST) — antes Admin2022 la
    pedía en `web/catalog/servicios/` (misma lógica que
    catalog.api.web.views.ServiciosWebView)."""

    def get(self, request, format=None):
        todas = request.GET.get("todas")
        return Response(ServicioSerializer(services.list_servicios(todas=bool(todas)), many=True).data)

    def post(self, request, format=None):
        _, data = services.crear_servicio(
            request.POST.get("nombre"), request.POST.get("descripcion"),
            request.POST.get("categoria"), request.FILES.get("foto"),
        )
        return Response(data)


class ProfesionesAdminView(AdminAPIView):
    """Sirve tanto `profesiones/<pk>` (DELETE) como `profesion/<pk>` (GET,
    singular) — dos URLs distintas que delegan a esta misma clase. La ruta
    base `profesiones/` (GET+POST+PUT) vive en ProfesionesListAdminView."""

    def get(self, request, pk, format=None):
        return Response(ProfesionSerializer(services.obtener_profesion(pk)).data)

    def delete(self, request, pk, format=None):
        services.eliminar_profesion(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfesionesListAdminView(AdminAPIView):
    """Ruta base `admin/catalog/profesiones/` (GET+POST+PUT) — antes
    Admin2022 la pedía en `web/catalog/profesiones/` (misma lógica que
    catalog.api.web.views.ProfesionesWebView)."""

    def get(self, request, format=None):
        return Response(ProfesionSerializer(services.list_profesiones_activas(), many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_profesion(
            request.data.get("nombre"), request.data.get("descripcion"),
            request.data.get("servicio"), request.FILES.get("foto"),
        ))

    def put(self, request, format=None):
        data, valido = services.actualizar_profesion(
            request.data.get("id"), request.data.get("servicio"), request.data
        )
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)


class CiudadesAdminView(AdminAPIView):
    """El panel admin llama también un PUT a `ciudades/` que no está
    implementado en el backend (405 esperado) — decisión de producto
    pendiente, no agregar sin confirmar el comportamiento deseado."""

    def post(self, request, format=None):
        data, valido = services.crear_ciudad(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_201_CREATED)


class SolicitudesProfesionAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.listar_solicitudes_profesion())
        if page is not None:
            return self.get_paginated_response(SolicitudProfesionSerializer(page, many=True).data)


class SolicitudPorUsuarioAdminView(AdminAPIView):
    def get(self, request, user, format=None):
        return Response(SolicitudProfesionSerializer(services.solicitudes_profesion_por_usuario(user), many=True).data)


class SolicitudProfesionDetalleAdminView(AdminAPIView):
    def get(self, request, pk, format=None):
        return Response(SolicitudProfesionSerializer(services.obtener_solicitud_profesion(pk)).data)


class ManejoSolicitudAdminView(AdminAPIView):
    """Sirve tres paths distintos por verbo: GET/POST en
    `obtener_solicitudes_profesiones/`/`crear_solicitud_profesion/`, y
    PUT/DELETE en `change-solicitud/<pk>` (este último usado activamente
    por el panel admin)."""

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
    def post(self, request, format=None):
        return Response(services.crear_profesiones_faltantes())


class ProfesionProveedorAdminView(AdminAPIView):
    def get(self, request, proveedor_id, format=None):
        return Response(Profesion_ProveedorSerializer(services.profesiones_por_proveedor(proveedor_id), many=True).data)


class CrearProfesionProveedorAdminView(AdminAPIView):
    """Usada al aceptar una SolicitudProfesion (ver
    catalog.api.admin.views.ManejoSolicitudAdminView): crea el
    Profesion_Proveedor real para el proveedor identificado por username."""

    def post(self, request, username, format=None):
        data, creada = services.crear_profesion_proveedor_por_username(username, request.data)
        if creada is not None:
            data["profesion_proveedor"] = Profesion_ProveedorSerializer(creada).data
        return Response(data)


class ProfesionProveedorDetalleAdminView(AdminAPIView):
    """El PUT es exclusivo del panel admin; el DELETE se conserva aunque
    no tenga llamador confirmado."""

    def put(self, request, pk, format=None):
        data, valido = services.actualizar_profesion_proveedor(pk, request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, pk, format=None):
        return Response(services.eliminar_profesion_proveedor(pk))


class SincronizarProfesionProveedorAdminView(AdminAPIView):
    def post(self, request, format=None):
        return Response(services.sincronizar_profesion_proveedor())


class SolicitudesProfesionBusquedaAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        page = self.paginate_queryset(services.buscar_solicitudes_profesion_por_nombre(user))
        if page is not None:
            return self.get_paginated_response(SolicitudProfesionSerializer(page, many=True).data)


class SolicitudesProfesionFechaAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        fecha_inicio = datetime.datetime.strptime(request.GET.get("fechaInicio"), "%Y-%m-%d")
        fecha_fin = datetime.datetime.strptime(request.GET.get("fechaFin"), "%Y-%m-%d")
        page = self.paginate_queryset(services.filtrar_solicitudes_profesion_por_fecha(fecha_inicio, fecha_fin))
        if page is not None:
            return self.get_paginated_response(SolicitudProfesionSerializer(page, many=True).data)
