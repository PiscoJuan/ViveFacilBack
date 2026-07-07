from rest_framework.response import Response

from api.serializers import NotificacionMasivaSerializer
from core.views import ProveedorAPIView
from notifications import services


class NotificacionAnuncioProveedorView(ProveedorAPIView):
    """Endpoint propio del proveedor para notificacion-anuncio — antes
    pedía directo a `web/notifications/notificacion-anuncio/`
    (notifications.api.web.views.NotificacionAnuncioWebView)."""

    def get(self, request, format=None):
        return Response(NotificacionMasivaSerializer(services.list_notificaciones_masivas(), many=True).data)


class NotificacionChatProveedorView(ProveedorAPIView):

    def post(self, request, format=None):
        data, http_status = services.notificar_chat_proveedor(
            request.data.get("remitente"),
            request.data.get("user"),
            request.data.get("message"),
            request.data.get("url"),
        )
        return Response(data, status=http_status)
