from rest_framework.response import Response

from api.serializers import NotificacionMasivaSerializer
from core.views import SolicitanteAPIView
from notifications import services


class NotificacionAnuncioSolicitanteView(SolicitanteAPIView):
    """Endpoint propio del solicitante para notificacion-anuncio — antes
    pedía una ruta sin ningún prefijo de rol.

    Filtrado por servidor igual que el del proveedor: solo las enviadas después
    de su registro y dirigidas a su app."""

    def get(self, request, format=None):
        notificaciones = services.notificaciones_visibles(request.user)
        return Response(NotificacionMasivaSerializer(notificaciones, many=True).data)


class NotificacionChatSolicitanteView(SolicitanteAPIView):
    """Confirmado por grep exclusivo de Solicitante2022
    (`chat.service.ts:127`, que además hardcodeaba la URL completa de
    producción en vez de usar `API_URL` — normalizado de paso al migrar,
    tal cual lo anotaba `05-fase-3-solicitante.md`). Antes sin ningún
    permission_classes (abierto)."""

    def post(self, request, format=None):
        data = services.notificar_chat_solicitante(
            request.data.get("remitente"), request.data.get("isSolicitante"),
            request.data.get("message"), request.data.get("user"), request.data.get("url"),
        )
        return Response(data)
