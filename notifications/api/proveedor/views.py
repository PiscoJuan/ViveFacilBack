from rest_framework.response import Response
from rest_framework import status

from api.serializers import NotificacionMasivaSerializer
from core.views import ProveedorAPIView
from notifications import services


class NotificacionAnuncioProveedorView(ProveedorAPIView):
    """Endpoint propio del proveedor para notificacion-anuncio — antes
    pedía directo a `web/notifications/notificacion-anuncio/`
    (notifications.api.web.views.NotificacionAnuncioWebView).

    Devuelve solo lo que le corresponde a este proveedor (fecha de registro,
    app destino y profesión). Antes devolvía la tabla entera y la app filtraba
    en el cliente."""

    def get(self, request, format=None):
        notificaciones = services.notificaciones_visibles(request.user)
        return Response(NotificacionMasivaSerializer(notificaciones, many=True).data)


class NotificacionFeedProveedorView(ProveedorAPIView):
    """Feed unificado de la pestaña Notificaciones: masivas (con estado por
    usuario) + eventos individuales (solicitud, pago...), con pestañas
    Todas/No leídas/Leídas resueltas del lado del cliente sobre lo que
    devuelve acá."""

    def get(self, request, format=None):
        items, counts = services.feed_notificaciones(request.user)
        return Response({"items": items, "counts": counts})


class NotificacionFeedLeidaProveedorView(ProveedorAPIView):

    def post(self, request, tipo, id, format=None):
        try:
            services.marcar_leida(request.user, tipo, id)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificacionFeedOcultarProveedorView(ProveedorAPIView):
    """"Eliminar notificación" desde la app: oculta para este usuario, nunca
    borra la fila compartida de una masiva."""

    def delete(self, request, tipo, id, format=None):
        try:
            services.ocultar_notificacion(request.user, tipo, id)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificacionChatProveedorView(ProveedorAPIView):

    def post(self, request, format=None):
        data, http_status = services.notificar_chat_proveedor(
            request.data.get("remitente"),
            request.data.get("user"),
            request.data.get("message"),
            request.data.get("url"),
        )
        return Response(data, status=http_status)
