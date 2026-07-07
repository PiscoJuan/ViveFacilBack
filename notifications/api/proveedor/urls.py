from django.urls import path

from notifications.api.proveedor.views import NotificacionAnuncioProveedorView, NotificacionChatProveedorView

urlpatterns = [
    path("chat/", NotificacionChatProveedorView.as_view()),
    path("notificacion-anuncio/", NotificacionAnuncioProveedorView.as_view()),
]
