from django.urls import path

from notifications.api.admin.views import (
    CorreoSolicitudAdminView,
    EmailBienvenidaAdminView,
    EnviarAlertaAdminView,
    NotificacionAnuncioAdminView,
    NotificacionAnuncioDetalleAdminView,
    NotificacionesAdminView,
    NotificacionesDetalleAdminView,
    NotificacionGeneralAdminView,
)

urlpatterns = [
    path("notificaciones/", NotificacionesAdminView.as_view()),
    path("notificaciones/<str:id>/", NotificacionesAdminView.as_view()),
    path("notificaciones/estado/", NotificacionesDetalleAdminView.as_view()),
    path("notificaciones/envio/", NotificacionesDetalleAdminView.as_view()),
    path("notificacion-anuncio/", NotificacionAnuncioAdminView.as_view()),
    path("notificacion-anuncio/estado/", NotificacionAnuncioDetalleAdminView.as_view()),  # antes que <str:id>/
    path("notificacion-anuncio/envio/", NotificacionAnuncioDetalleAdminView.as_view()),  # antes que <str:id>/
    path("notificacion-anuncio/<str:id>/", NotificacionAnuncioAdminView.as_view()),
    path("email-bienvenida/", EmailBienvenidaAdminView.as_view()),
    path("correo-solicitud/", CorreoSolicitudAdminView.as_view()),
    path("enviar-alerta/<str:user_email>/<str:asunto>/<str:texto>", EnviarAlertaAdminView.as_view()),
    path("notificacion-general/", NotificacionGeneralAdminView.as_view()),
]
