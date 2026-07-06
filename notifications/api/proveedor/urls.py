from django.urls import path

from notifications.api.proveedor.views import NotificacionChatProveedorView

urlpatterns = [
    path("chat/", NotificacionChatProveedorView.as_view()),
]
