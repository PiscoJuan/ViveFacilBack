from django.urls import path

from accounts.api.proveedor.views import (
    CambioContraseniaProveedorView,
    ChangePasswordProveedorView,
    CompleteDataUserProveedorView,
    DatosUsuarioProveedorView,
    DatoProveedorView,
    DispositivoNotificacionProveedorView,
    DocumentoProveedorView,
    LoginProveedorView,
    ProveedorPorCorreoProveedorView,
    ProveedorRegistroManualView,
    RegistroProveedorView,
    SolicitanteByUserDatosProveedorView,
    VersionAndroidProveedorView,
    VersionIosProveedorView,
)

urlpatterns = [
    path("login/", LoginProveedorView.as_view()),
    path("cambiocontrasenia/", CambioContraseniaProveedorView.as_view()),
    path("dispositivos-notificacion/", DispositivoNotificacionProveedorView.as_view()),
    path("dispositivos-notificacion/token/", DispositivoNotificacionProveedorView.as_view()),
    path("registro/", RegistroProveedorView.as_view()),
    path("registro-manual/", ProveedorRegistroManualView.as_view()),
    path("documentos/<str:username>/", DocumentoProveedorView.as_view()),
    path("datos/<str:user>/", DatoProveedorView.as_view()),
    path("version/android/", VersionAndroidProveedorView.as_view()),
    path("version/ios/", VersionIosProveedorView.as_view()),
    path("solicitante-por-datos/<str:UserDatosId>", SolicitanteByUserDatosProveedorView.as_view()),
    path("reactivar/<str:access_security>", ChangePasswordProveedorView.as_view()),
    path("dato-usuario/<str:id>", DatosUsuarioProveedorView.as_view()),
    path("completar-datos/<str:username>/", CompleteDataUserProveedorView.as_view()),
    path("datos-proveedor/<str:user>", ProveedorPorCorreoProveedorView.as_view()),
]
