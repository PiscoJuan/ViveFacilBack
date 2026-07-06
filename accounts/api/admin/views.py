from rest_framework import status
from rest_framework.response import Response

from accounts import services
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.permissions import IsPublic
from core.views import AdminAPIView


class LoginAdminView(AdminAPIView):
    """Vista delgada de AuthService para el rol Administrador — mismo
    mecanismo que LoginSolicitanteView/LoginProveedorView (Fase 3/4).
    Reemplaza el branching manual que hoy vive en `LoginAdmin.post()`
    (api/views.py:3198). Ver la rama `expected_role == "Administrador"` en
    `accounts.services.authenticate_login` para la réplica exacta del caso
    "cuenta deshabilitada", que difiere del de Proveedor/Solicitante."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        username = request.data.get("username")
        password = request.data.get("password")
        data, http_status = services.authenticate_login(
            request, username, password, expected_role="Administrador"
        )
        return Response(data, status=http_status)


# ---------------------------------------------------------------------------
# Fase 5, Bloque 2 — gestión de cuentas y usuarios
# ---------------------------------------------------------------------------

class AdministradoresAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Administradores (api/views.py:2442). Antes sin ningún
    permission_classes."""

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


class AdminDetailsAdminView(AdminAPIView):
    """Réplica de Admin_Details (api/views.py:2540)."""

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
    """Réplica de Solicitantes (api/views.py:2360). Antes sin ningún
    permission_classes."""

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
    """Réplica de Proveedores (api/views.py:1637). Antes sin ningún
    permission_classes."""

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
    """Réplica de Proveedores_Pendientes (api/views.py:1995)."""

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
    """Réplica de Proveedores_Pendientes_Details (api/views.py:1069)."""

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
    """Réplica de Proveedores_Pendientes_Estado (api/views.py:1149)."""

    def put(self, request, format=None):
        services.pendiente_aprobar_por_id(request.GET.get("id"))
        return Response(status=status.HTTP_200_OK)


class ProveedoresPendientesRechazoAdminView(AdminAPIView):
    """Réplica de Proveedores_Pendientes_Details2 (api/views.py:1158)."""

    def put(self, request, pk, format=None):
        services.pendiente_rechazar(pk, request.data.get("razon"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresRechazadosAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Proveedores_Rechazados (api/views.py:2082)."""

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
    """Réplica de Proveedores_Rechazados_Details (api/views.py:1331)."""

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
    """Réplica de Proveedores_Proveedores (api/views.py:2171). Ver
    accounts.services.listar_proveedores_proveedores_queryset para el
    hallazgo del efecto secundario de import que esta clase dispara en
    api/views.py (no se toca, no se duplica)."""

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
    """Réplica de Proveedores_Proveedores_Details (api/views.py:1173)."""

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
    """Réplica de ProveedorDeleteView (api/views.py:1308)."""

    def delete(self, request, proveedor_id, format=None):
        eliminadas = services.eliminar_proveedor_cascade(proveedor_id)
        return Response({
            "message": "Proveedor, solicitudes y envíos eliminados exitosamente.",
            "solicitudes_eliminadas": eliminadas,
        }, status=status.HTTP_204_NO_CONTENT)


class ProveedorEdicionAdminView(AdminAPIView):
    """Réplica de ProveedorEdicion (api/views.py:4004). Confirmado por grep
    que lo llama Admin2022, no Provedor2022, pese al nombre."""

    def put(self, request, format=None):
        data, http_status = services.editar_proveedor_admin(request.data, request.FILES)
        return Response(data, status=http_status)


class PendientesDocumentsAdminView(AdminAPIView):
    """Réplica de PendientesDocumentsView (api/views.py:3882)."""

    def get(self, request, format=None):
        from api.serializers import PendientesDocumentsSerializer
        return Response(PendientesDocumentsSerializer(services.listar_documentos_pendientes(), many=True).data)

    def delete(self, request, format=None):
        services.eliminar_documento_pendiente_por_id(request.GET.get("id"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProveedoresDocumentsAdminView(AdminAPIView):
    """Réplica de ProveedoresDocumentsView (api/views.py:1966)."""

    def get(self, request, format=None):
        from api.serializers import DocumentSerializer
        return Response(DocumentSerializer(services.listar_documentos_proveedores(), many=True).data)

    def delete(self, request, format=None):
        services.eliminar_documento_proveedor_por_id(request.GET.get("id"))
        return Response(status=status.HTTP_204_NO_CONTENT)


class RolesPermisosAdminView(AdminAPIView):
    """Réplica de RolesPermisos (api/views.py:4252). No es scaffolding, ya
    hace CRUD real de Group/Permission — ver docs/refactor/07-fase-5-admin.md.
    Ver accounts.services.actualizar_permisos_grupo para un hallazgo real de
    lógica invertida en el PUT, preservado tal cual."""

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
    """Réplica de Permisos (api/views.py:4300)."""

    def get(self, request, format=None):
        from api.serializers import PermissionSerializer
        return Response(PermissionSerializer(services.listar_permisos_queryset(), many=True).data)


class GruposAdminView(AdminAPIView):
    """Réplica de Grupos (api/views.py:3349) — lista simple de todos los
    Group, distinto de RolesPermisosAdminView (que busca uno por nombre)."""

    def get(self, request, format=None):
        from api.serializers import GroupSerializer
        return Response(GroupSerializer(services.listar_grupos_queryset(), many=True).data)


# ---------------------------------------------------------------------------
# Cleanup post-Fase-5 — cierre del checklist maestro (endpoints no cubiertos
# por las tablas de Fase 3/4/5), Bloque 1: auth/social/password/versionamiento.
# ---------------------------------------------------------------------------

class SolicitanteUserAdminView(AdminAPIView):
    """Réplica de SolicitanteUser.get (api/views.py:1639-1645), endpoint
    multi-rol (ver SolicitanteUserSolicitanteView en
    accounts/api/solicitante/views.py) — confirmado usado por Admin2022
    (`pendientes.component.ts`, búsqueda de un solicitante por correo)."""

    def get(self, request, user, format=None):
        from api.serializers import SolicitanteSerializer

        serializer = SolicitanteSerializer(services.obtener_solicitante_por_email(user), many=True)
        return Response(serializer.data)


class AdminUserView(AdminAPIView):
    """Réplica de AdminUser.get (api/views.py:2539-2546). Definida en el
    service de Admin2022 (`obtener_admin_user`) pero sin ningún llamador
    real (grep sobre componentes) — el login real de Admin2022 pasa por
    Firebase directo, no por este mecanismo (ver Fase 5, Bloque 4 y
    AdminUserPassView de abajo)."""

    def get(self, request, user, format=None):
        return Response(services.obtener_admin_por_email(user))


class AdminUserPassView(AdminAPIView):
    """Réplica de AdminUserPass.post (api/views.py:2549-...). Sin llamador
    real (ver AdminUserView) — segundo mecanismo de login de administrador,
    no consolidado con `authenticate_login`. Público (IsPublic): es login,
    no puede exigir sesión previa."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data = services.autenticar_admin_user_pass(
            request.data.get("username"), request.data.get("password"), request)
        if data is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(data)


class LogoutAdminView(AdminAPIView):
    """Réplica de Logout (api/views.py:639-645). Sin evidencia de llamador
    real en ningún frontend (grep fresco: Admin2022 define el wrapper en
    python-anywhere.service.ts pero ningún componente lo invoca; su logout
    real es Firebase `signOut`, mismo patrón que LoginAdmin/AdminUser —
    ver docs/refactor/07-fase-5-admin.md y checklist). Se preserva público
    (IsPublic, igual que el original sin permission_classes): es una acción
    de cierre de sesión por token explícito en la URL, no requiere estar
    ya autenticado vía DRF."""

    permission_classes = [IsPublic]

    def get(self, request, token, format=None):
        services.cerrar_sesion(request, token)
        return Response(status=status.HTTP_200_OK)


class ActualizarCaducidadAdminView(AdminAPIView):
    """Réplica de ActualizarCaducidad (api/views.py:2856-2882). Confirmado
    real, exclusivo de Admin2022 (`proveedores.component.ts`). Endurecimiento
    real: antes sin permission_classes."""

    def put(self, request, pk, format=None):
        try:
            fecha = services.actualizar_caducidad_proveedor(pk, request.data)
            return Response(fecha)
        except Exception as e:
            return Response("error: " + str(e))


class ActualizarCaducidadProveedoresAdminView(AdminAPIView):
    """Réplica de ActualizarCaducidadProveedoresRequest (api/views.py:2929-2948).
    Sin evidencia de llamador real en ningún frontend — probable trigger
    manual o cron externo a este repo. DELIBERADAMENTE se preserva público
    (IsPublic, no IsAdministrador): endurecerlo sin poder confirmar si algo
    externo lo golpea sin sesión rompería esa integración en silencio. Ver
    docs/refactor/CHECKLIST-inventario-endpoints.md."""

    permission_classes = [IsPublic]

    def get(self, request, format=None):
        data, http_status = services.actualizar_caducidad_masiva_proveedores()
        return Response(data, status=http_status)


class DatosAdminView(AdminAPIView):
    """Réplica de DatosUsers (api/views.py:1364-1382). Sin evidencia de
    llamador real en ningún frontend — se migra igual por consistencia."""

    def get(self, request, format=None):
        from api.serializers import DatosSerializer
        return Response(DatosSerializer(services.listar_datos_queryset(), many=True).data)

    def delete(self, request, format=None):
        return Response(services.eliminar_dato_por_id(request.GET.get("id")))


class UsuariosAdminView(AdminAPIView):
    """Réplica de Usuarios (api/views.py:1385-1403). Sin evidencia de
    llamador real en ningún frontend."""

    def get(self, request, format=None):
        from api.serializers import UserSerializer
        return Response(UserSerializer(services.listar_usuarios_queryset(), many=True).data)

    def delete(self, request, format=None):
        return Response(services.eliminar_usuario_por_id(request.GET.get("id")))


class ProveedoresSearchAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Proveedores_Search_Name (api/views.py:1249-1261). Sin
    evidencia de llamador real en ningún frontend."""

    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        from api.serializers import ProveedorSerializer
        page = self.paginate_queryset(services.buscar_proveedores_por_nombre_queryset(user))
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)


class ProveedoresFilterDateAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Proveedores_Filter_Date (api/views.py:1264-1279). Sin
    evidencia de llamador real en ningún frontend."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import ProveedorSerializer
        page = self.paginate_queryset(services.filtrar_proveedores_por_fecha_queryset(
            request.GET.get("fechaInicio"), request.GET.get("fechaFin")))
        if page is not None:
            return self.get_paginated_response(ProveedorSerializer(page, many=True).data)


class SolicitantesFilterAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de SolicitantesFilter (api/views.py:1452-1466). Confirmado
    real, exclusivo de Admin2022."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import SolicitanteSerializer
        page = self.paginate_queryset(services.filtrar_solicitantes_por_fecha_queryset(
            request.GET.get("fechaInicio"), request.GET.get("fechaFin")))
        if page is not None:
            return self.get_paginated_response(SolicitanteSerializer(page, many=True).data)


class FiltroNombresAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de FiltroNombres (api/views.py:1469-1481). Confirmado real,
    exclusivo de Admin2022."""

    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        from api.serializers import SolicitanteSerializer
        page = self.paginate_queryset(services.buscar_solicitantes_por_nombre_queryset(user))
        if page is not None:
            return self.get_paginated_response(SolicitanteSerializer(page, many=True).data)


class PendientesSearchAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Pendientes_Search_Name (api/views.py:875-887). Confirmado
    real, exclusivo de Admin2022."""

    pagination_class = MyCustomPagination

    def get(self, request, user, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        page = self.paginate_queryset(services.buscar_proveedores_pendientes_por_nombre_queryset(user))
        if page is not None:
            return self.get_paginated_response(Proveedor_PendienteSerializer(page, many=True).data)


class PendientesFilterDateAdminView(AdminAPIView, MyPaginationMixin):
    """Réplica de Pendientes_FilterDate (api/views.py:890-905). Confirmado
    real, exclusivo de Admin2022."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        from api.serializers import Proveedor_PendienteSerializer
        page = self.paginate_queryset(services.filtrar_proveedores_pendientes_por_fecha_queryset(
            request.GET.get("fechaInicio"), request.GET.get("fechaFin")))
        if page is not None:
            return self.get_paginated_response(Proveedor_PendienteSerializer(page, many=True).data)


class UpdateProveedorPendienteAdminView(AdminAPIView):
    """Réplica de Update_Proveedor_Pendiente (api/views.py:665-729). Sin
    evidencia de llamador real en ningún frontend — se migra igual por
    consistencia."""

    def post(self, request, format=None):
        data, http_status = services.actualizar_datos_proveedor_pendiente(request.data)
        return Response(data, status=http_status)


class DataProveedorProveedorAdminView(AdminAPIView):
    """Réplica de Data_Proveedor_Proveedor (api/views.py:791-860). Confirmado
    real (POST), único consumidor Admin2022
    (`crear_proveedor_proveedor`). El `delete` original no captura ningún id
    de URL y solo hace `print("In process")` — no-op preexistente sin
    consumidor real, se preserva tal cual."""

    def post(self, request, format=None):
        return Response(services.crear_proveedor_proveedor_manual(request.data))

    def delete(self, request, format=None):
        return Response(status=status.HTTP_204_NO_CONTENT)


class GetAdminByUserAdminView(AdminAPIView):
    """Réplica de Get_AdminByUser (api/views.py:1137-1143). Confirmado real,
    exclusivo de Admin2022 (nombre de clase engañoso, ver
    accounts.services.obtener_admin_por_username)."""

    def get(self, request, user, format=None):
        from api.serializers import ProveedorSerializer
        return Response(ProveedorSerializer(services.obtener_admin_por_username(user)).data)
