from django.urls import path

from notifications.api.solicitante.views import (
    NotificacionAnuncioSolicitanteView,
    NotificacionChatSolicitanteView,
    NotificacionFeedLeidaSolicitanteView,
    NotificacionFeedOcultarSolicitanteView,
    NotificacionFeedSolicitanteView,
)

urlpatterns = [
    path("chat/", NotificacionChatSolicitanteView.as_view()),
    path("notificacion-anuncio/", NotificacionAnuncioSolicitanteView.as_view()),
    path("feed/", NotificacionFeedSolicitanteView.as_view()),
    path("feed/<str:tipo>/<int:id>/leer/", NotificacionFeedLeidaSolicitanteView.as_view()),
    path("feed/<str:tipo>/<int:id>/", NotificacionFeedOcultarSolicitanteView.as_view()),
]
