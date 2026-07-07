from rest_framework import status
from rest_framework.response import Response

from accounts import services
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.permissions import IsPublic
from core.views import AdminAPIView


class LoginAdminView(AdminAPIView):
    """El caso "cuenta deshabilitada" para Administrador devuelve 200 con
    `active=False` en vez de 400 — distinto del comportamiento para
    Proveedor/Solicitante. Ver la rama `expected_role == "Administrador"` en
    `accounts.services.authenticate_login`."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        username = request.data.get("username")
        password = request.data.get("password")
        data, http_status = services.authenticate_login(
            request, username, password, expected_role="Administrador"
        )
        return Response(data, status=http_status)


class AdministradoresAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import AdministradorSerializer
        page = self.paginate_queryset(services.listar_administradores_queryset())
        if page is not None:
            return self.get_paginated_response(AdministradorSerializer(page, many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_administrador(request.data, request.FILES.get("foto")))

    def put(self, request, format=None):
        services.cambiar_estado_administrador(request.GET.get("id"), request.data.get("estado"))
        return Response(status=status.HTTP_200_OK)

    def delete(self, request, id, format=None):
        services.eliminar_administrador(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdministradoresFilterAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(
            services.administradores_por_rango_fecha_queryset(
                request.GET.get("fechaInicio"), request.GET.get("fechaFin")
            )
        )
        if page is not None:
            from api.serializers import AdministradorSerializer
            return self.get_paginated_response(AdministradorSerializer(page, many=True).data)


class AdministradoresUserAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        page = self.paginate_queryset(services.administradores_por_nombre_queryset(user))
        if page is not None:
            from api.serializers import AdministradorSerializer
            return self.get_paginated_response(AdministradorSerializer(page, many=True).data)


class AdminDetailsAdminView(AdminAPIView):
    def get(self, request, pk, format=None):
        from api.serializers import AdministradorSerializer
        return Response(AdministradorSerializer(services.obtener_administrador(pk)).data)

    def put(self, request, pk, format=None):
        data, http_status = services.actualizar_administrador(pk, request.data, request.FILES)
        return Response(data, status=http_status)

    def delete(self, request, pk, format=None):
        services.eliminar_administrador(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SolicitantesAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import SolicitanteSerializer
        page = self.paginate_queryset(services.listar_solicitantes_queryset(request.GET.get("filtro")))
        if page is not None:
            return self.get_paginated_response(SolicitanteSerializer(page, many=True).data)

    def put(self, request, id, format=None):
        data, http_status = services.actualizar_solicitante(id, request.data)
        return Response(data, status=http_status)

    def delete(self, request, id, format=None):
        services.eliminar_solicitante(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import ProveedorSerializer
        page = self.paginate_queryset(services.listar_proveedores_queryset())
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)

    def put(self, request, id, format=None):
        data, http_status = services.actualizar_proveedor(id, request.data)
        return Response(data, status=http_status)

    def delete(self, request, id, format=None):
        services.desactivar_proveedor(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresPendientesAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        page = self.paginate_queryset(services.listar_proveedores_pendientes_queryset())
        if page is not None:
            return self.get_paginated_response(Proveedor_PendienteSerializer(page, many=True).data)

    def put(self, request, format=None):
        data, http_status = services.actualizar_descripcion_documento_pendiente_admin(
            request.data.get("descripcion"), request.data.get("profesion"))
        return Response(data, status=http_status)

    def delete(self, request, username, desc, format=None):
        data, http_status = services.eliminar_documento_pendiente_admin(username, desc)
        return Response(data, status=http_status)


class ProveedoresPendientesDetailsAdminView(AdminAPIView):
    def get(self, request, pk, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        return Response(Proveedor_PendienteSerializer(services.obtener_proveedor_pendiente(pk)).data)

    def put(self, request, pk, format=None):
        data, http_status = services.actualizar_proveedor_pendiente_detalle(pk, request.data, request.FILES)
        return Response(data, status=http_status)

    def delete(self, request, pk, format=None):
        services.pendiente_marcar_procesado(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresPendientesEstadoAdminView(AdminAPIView):
    def put(self, request, format=None):
        services.pendiente_aprobar_por_id(request.GET.get("id"))
        return Response(status=status.HTTP_200_OK)


class ProveedoresPendientesRechazoAdminView(AdminAPIView):
    def put(self, request, pk, format=None):
        services.pendiente_rechazar(pk, request.data.get("razon"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresRechazadosAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        page = self.paginate_queryset(services.listar_proveedores_rechazados_queryset())
        if page is not None:
            return self.get_paginated_response(Proveedor_PendienteSerializer(page, many=True).data)

    def put(self, request, format=None):
        data, http_status = services.actualizar_descripcion_documento_pendiente_admin(
            request.data.get("descripcion"), request.data.get("profesion"))
        return Response(data, status=http_status)

    def delete(self, request, username, desc, format=None):
        data, http_status = services.eliminar_documento_pendiente_admin(username, desc)
        return Response(data, status=http_status)


class ProveedoresRechazadosDetailsAdminView(AdminAPIView):
    def get(self, request, pk, format=None):
        from api.serializers import Proveedor_PendienteSerializer2
        return Response(Proveedor_PendienteSerializer2(services.obtener_proveedor_rechazado(pk)).data)

    def put(self, request, pk, format=None):
        data, http_status = services.actualizar_proveedor_rechazado_detalle(pk, request.data, request.FILES)
        return Response(data, status=http_status)

    def delete(self, request, pk, format=None):
        services.rechazado_revertir_a_pendiente(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresProveedoresAdminView(AdminAPIView, MyPaginationMixin):
    """El listado depende de un efecto secundario de import en
    api/views.py (escaneo de caducidad a nivel de módulo) que no se
    duplica acá — ver accounts.services.listar_proveedores_proveedores_queryset."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import ProveedorSerializer
        page = self.paginate_queryset(services.listar_proveedores_proveedores_queryset())
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)

    def put(self, request, format=None):
        data, http_status = services.actualizar_descripcion_documento_pendiente_admin(
            request.data.get("descripcion"), request.data.get("profesion"))
        return Response(data, status=http_status)

    def delete(self, request, username, desc, format=None):
        data, http_status = services.eliminar_documento_pendiente_admin(username, desc)
        return Response(data, status=http_status)


class ProveedoresProveedoresDetailsAdminView(AdminAPIView):
    def get(self, request, pk, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        return Response(Proveedor_PendienteSerializer(services.obtener_proveedor_proveedores_detalle(pk)).data)

    def put(self, request, pk, format=None):
        data, http_status = services.actualizar_proveedor_proveedores_detalle(pk, request.data, request.FILES)
        return Response(data, status=http_status)

    def delete(self, request, pk, format=None):
        services.pendiente_marcar_procesado(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedorDeleteAdminView(AdminAPIView):
    def delete(self, request, proveedor_id, format=None):
        eliminadas = services.eliminar_proveedor_cascade(proveedor_id)
        return Response({
            "message": "Proveedor, solicitudes y envíos eliminados exitosamente.",
            "solicitudes_eliminadas": eliminadas,
        }, status=status.HTTP_204_NO_CONTENT)


class ProveedorEdicionAdminView(AdminAPIView):
    """Pese al nombre, esta vista es de uso exclusivo de Admin2022, no de
    Proveedor."""

    def put(self, request, format=None):
        data, http_status = services.editar_proveedor_admin(request.data, request.FILES)
        return Response(data, status=http_status)


class PendientesDocumentsAdminView(AdminAPIView):
    def get(self, request, format=None):
        from api.serializers import PendientesDocumentsSerializer
        return Response(PendientesDocumentsSerializer(services.listar_documentos_pendientes(), many=True).data)

    def delete(self, request, format=None):
        services.eliminar_documento_pendiente_por_id(request.GET.get("id"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresDocumentsAdminView(AdminAPIView):
    def get(self, request, format=None):
        from api.serializers import DocumentSerializer
        return Response(DocumentSerializer(services.listar_documentos_proveedores(), many=True).data)

    def delete(self, request, format=None):
        services.eliminar_documento_proveedor_por_id(request.GET.get("id"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolesPermisosAdminView(AdminAPIView):
    """El PUT delega en `accounts.services.actualizar_permisos_grupo`, que
    tiene una lógica de sincronización de permisos invertida — ver
    docstring de esa función."""

    def get(self, request, id, format=None):
        from api.serializers import GroupSerializer
        return Response(GroupSerializer(services.obtener_grupo_por_nombre(id)).data)

    def post(self, request, format=None):
        from api.serializers import GroupSerializer
        grupo = services.crear_grupo_con_permisos(request.data.get("nombre"), request.POST.getlist("permisos"))
        return Response(GroupSerializer(grupo).data)

    def put(self, request, format=None):
        from api.serializers import GroupSerializer
        grupo = services.actualizar_permisos_grupo(request.data.get("id"), request.POST.getlist("permisos"))
        return Response(GroupSerializer(grupo).data, status=status.HTTP_200_OK)

    def delete(self, request, id, format=None):
        services.eliminar_grupo(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class PermisosAdminView(AdminAPIView):
    def get(self, request, format=None):
        from api.serializers import PermissionSerializer
        return Response(PermissionSerializer(services.listar_permisos_queryset(), many=True).data)


class GruposAdminView(AdminAPIView):
    """Lista todos los Group; a diferencia de RolesPermisosAdminView, que
    busca uno por nombre."""

    def get(self, request, format=None):
        from api.serializers import GroupSerializer
        return Response(GroupSerializer(services.listar_grupos_queryset(), many=True).data)


class SolicitanteUserAdminView(AdminAPIView):
    """Endpoint multi-rol: comparte lógica con SolicitanteUserSolicitanteView
    (accounts/api/solicitante/views.py). Usado por Admin2022 para buscar un
    solicitante por correo."""

    def get(self, request, user, format=None):
        from api.serializers import SolicitanteSerializer

        serializer = SolicitanteSerializer(services.obtener_solicitante_por_email(user), many=True)
        return Response(serializer.data)


class AdminUserView(AdminAPIView):
    """Sin llamador real conocido: el login de Admin2022 pasa por Firebase
    directo, no por este mecanismo (ver AdminUserPassView)."""

    def get(self, request, user, format=None):
        return Response(services.obtener_admin_por_email(user))


class AdminUserPassView(AdminAPIView):
    """Sin llamador real conocido (ver AdminUserView) — mecanismo de login
    alternativo, no consolidado con `authenticate_login`. Público
    (IsPublic): es login, no puede exigir sesión previa."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data = services.autenticar_admin_user_pass(
            request.data.get("username"), request.data.get("password"), request)
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(data)


class LogoutAdminView(AdminAPIView):
    """Sin evidencia de uso real: el logout real de Admin2022 usa Firebase
    `signOut`. Público (IsPublic): es un cierre de sesión por token
    explícito en la URL, no requiere estar ya autenticado vía DRF."""

    permission_classes = [IsPublic]

    def get(self, request, token, format=None):
        services.cerrar_sesion(request, token)
        return Response(status=status.HTTP_200_OK)


class ActualizarCaducidadAdminView(AdminAPIView):
    """Confirmado real, exclusivo de Admin2022 (`proveedores.component.ts`).
    Exige IsAdministrador (heredado de AdminAPIView)."""

    def put(self, request, pk, format=None):
        try:
            fecha = services.actualizar_caducidad_proveedor(pk, request.data)
            return Response(fecha)
        except Exception as e:
            return Response("error: " + str(e))


class ActualizarCaducidadProveedoresAdminView(AdminAPIView):
    """Sin evidencia de llamador real en ningún frontend — probable trigger
    manual o cron externo a este repo. Se mantiene público (IsPublic, no
    IsAdministrador) a propósito: endurecerlo sin poder confirmar si algo
    externo lo golpea sin sesión rompería esa integración en silencio."""

    permission_classes = [IsPublic]

    def get(self, request, format=None):
        data, http_status = services.actualizar_caducidad_masiva_proveedores()
        return Response(data, status=http_status)


class DatosAdminView(AdminAPIView):
    def get(self, request, format=None):
        from api.serializers import DatosSerializer
        return Response(DatosSerializer(services.listar_datos_queryset(), many=True).data)

    def delete(self, request, format=None):
        return Response(services.eliminar_dato_por_id(request.GET.get("id")))


class UsuariosAdminView(AdminAPIView):
    def get(self, request, format=None):
        from api.serializers import UserSerializer
        return Response(UserSerializer(services.listar_usuarios_queryset(), many=True).data)

    def delete(self, request, format=None):
        return Response(services.eliminar_usuario_por_id(request.GET.get("id")))


class ProveedoresSearchAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        from api.serializers import ProveedorSerializer
        page = self.paginate_queryset(services.buscar_proveedores_por_nombre_queryset(user))
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)


class ProveedoresFilterDateAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import ProveedorSerializer
        page = self.paginate_queryset(services.filtrar_proveedores_por_fecha_queryset(
            request.GET.get("fechaInicio"), request.GET.get("fechaFin")))
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)


class SolicitantesFilterAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import SolicitanteSerializer
        page = self.paginate_queryset(services.filtrar_solicitantes_por_fecha_queryset(
            request.GET.get("fechaInicio"), request.GET.get("fechaFin")))
        if page is not None:
            return self.get_paginated_response(SolicitanteSerializer(page, many=True).data)


class FiltroNombresAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        from api.serializers import SolicitanteSerializer
        page = self.paginate_queryset(services.buscar_solicitantes_por_nombre_queryset(user))
        if page is not None:
            return self.get_paginated_response(SolicitanteSerializer(page, many=True).data)


class PendientesSearchAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        page = self.paginate_queryset(services.buscar_proveedores_pendientes_por_nombre_queryset(user))
        if page is not None:
            return self.get_paginated_response(Proveedor_PendienteSerializer(page, many=True).data)


class PendientesFilterDateAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        page = self.paginate_queryset(services.filtrar_proveedores_pendientes_por_fecha_queryset(
            request.GET.get("fechaInicio"), request.GET.get("fechaFin")))
        if page is not None:
            return self.get_paginated_response(Proveedor_PendienteSerializer(page, many=True).data)


class UpdateProveedorPendienteAdminView(AdminAPIView):
    def post(self, request, format=None):
        data, http_status = services.actualizar_datos_proveedor_pendiente(request.data)
        return Response(data, status=http_status)


class DataProveedorProveedorAdminView(AdminAPIView):
    """`delete` es intencionalmente un no-op (no captura ningún id de URL):
    así era el original, no hay consumidor real que dependa de que borre
    algo."""

    def post(self, request, format=None):
        return Response(services.crear_proveedor_proveedor_manual(request.data))

    def delete(self, request, format=None):
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetAdminByUserAdminView(AdminAPIView):
    """Nombre engañoso: pese a "AdminByUser", devuelve datos de Proveedor,
    no de Administrador (ver accounts.services.obtener_admin_por_username)."""

    def get(self, request, user, format=None):
        from api.serializers import ProveedorSerializer
        return Response(ProveedorSerializer(services.obtener_admin_por_username(user)).data)


class RegistroAdminView(AdminAPIView):
    """Alta manual de cuenta desde el panel admin — misma lógica que
    `accounts.api.web.views.RegistroWebView` (un `ModelViewSet` por router,
    no una vista simple), llamada acá directo sin pasar por el router."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        return Response(services.crear_cuenta_registro(request.POST, request.FILES))


class ProveedorPendienteAdminView(AdminAPIView):
    """Alta manual de un proveedor pendiente desde el panel admin — misma
    lógica que `accounts.api.web.views.ProveedorPendienteWebView` (el
    formulario público "quiero ser proveedor"). Antes Admin2022 pegaba
    directo a esa ruta pública a propósito (ver
    docs/refactor/CHECKLIST-inventario-endpoints.md, fila 74); esta vista
    reemplaza esa decisión para que el panel admin no dependa de una ruta
    de otro rol."""

    def post(self, request, format=None):
        _, serializer = services.crear_proveedor_pendiente(request.data, request.FILES)
        return Response({"success": True, "serializer": serializer.data})
