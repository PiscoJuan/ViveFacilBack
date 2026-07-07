from django.urls import path

from accounts.api.admin.views import (
    AdminDetailsAdminView,
    AdministradoresAdminView,
    AdministradoresFilterAdminView,
    AdministradoresUserAdminView,
    ActualizarCaducidadAdminView,
    ActualizarCaducidadProveedoresAdminView,
    AdminUserPassView,
    AdminUserView,
    DataProveedorProveedorAdminView,
    DatosAdminView,
    FiltroNombresAdminView,
    GetAdminByUserAdminView,
    GruposAdminView,
    LoginAdminView,
    LogoutAdminView,
    PendientesDocumentsAdminView,
    PendientesFilterDateAdminView,
    PendientesSearchAdminView,
    PermisosAdminView,
    ProveedoresFilterDateAdminView,
    ProveedoresSearchAdminView,
    ProveedorDeleteAdminView,
    ProveedorEdicionAdminView,
    ProveedoresAdminView,
    ProveedoresDocumentsAdminView,
    ProveedoresPendientesAdminView,
    ProveedoresPendientesDetailsAdminView,
    ProveedoresPendientesEstadoAdminView,
    ProveedoresPendientesRechazoAdminView,
    ProveedoresProveedoresAdminView,
    ProveedoresProveedoresDetailsAdminView,
    ProveedoresRechazadosAdminView,
    ProveedoresRechazadosDetailsAdminView,
    ProveedorPendienteAdminView,
    RegistroAdminView,
    RolesPermisosAdminView,
    SolicitantesAdminView,
    SolicitantesFilterAdminView,
    SolicitanteUserAdminView,
    UpdateProveedorPendienteAdminView,
    UsuariosAdminView,
)

urlpatterns = [
    path("login/", LoginAdminView.as_view()),
    path("registro/", RegistroAdminView.as_view()),

    path("administradores/", AdministradoresAdminView.as_view()),
    path("administradores/fechas/", AdministradoresFilterAdminView.as_view()),  # antes que <str:id>/
    path("administradores/buscar/<str:user>/", AdministradoresUserAdminView.as_view()),
    path("administradores/<str:id>/", AdministradoresAdminView.as_view()),
    path("administrador/<str:pk>/", AdminDetailsAdminView.as_view()),

    path("solicitantes/", SolicitantesAdminView.as_view()),
    path("solicitantes/fechas/", SolicitantesFilterAdminView.as_view()),  # antes que <str:id>/, ver nota de orden abajo
    path("solicitantes/buscar/<str:user>/", FiltroNombresAdminView.as_view()),
    path("solicitantes/<str:id>/estado/", SolicitantesAdminView.as_view()),
    path("solicitantes/<str:id>/", SolicitantesAdminView.as_view()),

    path("proveedores/", ProveedoresAdminView.as_view()),
    path("proveedores/fechas/", ProveedoresFilterDateAdminView.as_view()),  # antes que <str:id>/
    path("proveedores/buscar/<str:user>/", ProveedoresSearchAdminView.as_view()),
    path("proveedores/<str:id>/", ProveedoresAdminView.as_view()),

    # Los paths literales de dos segmentos (`buscar/<user>/`, `fechas/`,
    # `actualizar-datos/`) van ANTES que `<str:username>/<str:desc>/` y
    # `<str:pk>/`, que si no los interceptan primero (Django resuelve en
    # orden de declaración).
    path("proveedores-pendientes/", ProveedoresPendientesAdminView.as_view()),
    path("proveedores-pendientes/crear/", ProveedorPendienteAdminView.as_view()),
    path("proveedores-pendientes/buscar/<str:user>/", PendientesSearchAdminView.as_view()),
    path("proveedores-pendientes/fechas/", PendientesFilterDateAdminView.as_view()),
    path("proveedores-pendientes/actualizar-datos/", UpdateProveedorPendienteAdminView.as_view()),
    path("proveedores-pendientes/<str:username>/<str:desc>/", ProveedoresPendientesAdminView.as_view()),
    path("proveedores-pendientes/<str:pk>/", ProveedoresPendientesDetailsAdminView.as_view()),
    path("proveedores-pendientes-estado/", ProveedoresPendientesEstadoAdminView.as_view()),
    path("proveedores-pendientes/<str:pk>/rechazo/", ProveedoresPendientesRechazoAdminView.as_view()),

    path("proveedores-rechazados/", ProveedoresRechazadosAdminView.as_view()),
    path("proveedores-rechazados/<str:pk>/", ProveedoresRechazadosDetailsAdminView.as_view()),

    path("proveedores-proveedores/", ProveedoresProveedoresAdminView.as_view()),
    path("proveedores-proveedores/<str:pk>/", ProveedoresProveedoresDetailsAdminView.as_view()),
    path("proveedores-proveedores/<str:proveedor_id>/eliminar/", ProveedorDeleteAdminView.as_view()),

    path("edicion-proveedor/", ProveedorEdicionAdminView.as_view()),

    path("documentos-pendientes/", PendientesDocumentsAdminView.as_view()),
    path("documentos-proveedores/", ProveedoresDocumentsAdminView.as_view()),

    path("roles-permisos/", RolesPermisosAdminView.as_view()),
    path("roles-permisos/<str:id>/", RolesPermisosAdminView.as_view()),
    path("permisos/", PermisosAdminView.as_view()),
    path("grupos/", GruposAdminView.as_view()),

    path("solicitante-por-usuario/<str:user>", SolicitanteUserAdminView.as_view()),
    path("admin-user/<str:user>", AdminUserView.as_view()),
    path("admin-user-pass/", AdminUserPassView.as_view()),
    path("logout/<str:token>", LogoutAdminView.as_view()),
    path("actualizar-caducidad/<str:pk>", ActualizarCaducidadAdminView.as_view()),
    path("actualizar-caducidad-proveedores/", ActualizarCaducidadProveedoresAdminView.as_view()),

    path("datos/", DatosAdminView.as_view()),
    path("usuarios/", UsuariosAdminView.as_view()),
    path("proveedor-proveedor/", DataProveedorProveedorAdminView.as_view()),
    path("datos-admin/<str:user>", GetAdminByUserAdminView.as_view()),
]
