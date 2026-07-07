from django.urls import path

from notifications.api.solicitante.views import NotificacionAnuncioSolicitanteView, NotificacionChatSolicitanteView

urlpatterns = [
    path("chat/", NotificacionChatSolicitanteView.as_view()),
    path("notificacion-anuncio/", NotificacionAnuncioSolicitanteView.as_view()),
]
