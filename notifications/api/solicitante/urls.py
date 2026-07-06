from django.urls import path

from notifications.api.solicitante.views import NotificacionChatSolicitanteView

urlpatterns = [
    path("chat/", NotificacionChatSolicitanteView.as_view()),
]
