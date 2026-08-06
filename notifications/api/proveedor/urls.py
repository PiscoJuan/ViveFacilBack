from django.urls import path

from notifications.api.proveedor.views import (
    NotificacionAnuncioProveedorView,
    NotificacionChatProveedorView,
    NotificacionFeedLeidaProveedorView,
    NotificacionFeedOcultarProveedorView,
    NotificacionFeedProveedorView,
)

urlpatterns = [
    path("chat/", NotificacionChatProveedorView.as_view()),
    path("notificacion-anuncio/", NotificacionAnuncioProveedorView.as_view()),
    path("feed/", NotificacionFeedProveedorView.as_view()),
    path("feed/<str:tipo>/<int:id>/leer/", NotificacionFeedLeidaProveedorView.as_view()),
    path("feed/<str:tipo>/<int:id>/", NotificacionFeedOcultarProveedorView.as_view()),
]
