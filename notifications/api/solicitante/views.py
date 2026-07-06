from rest_framework.response import Response

from core.views import SolicitanteAPIView
from notifications import services


class NotificacionChatSolicitanteView(SolicitanteAPIView):
    """Réplica de Notificacion_Chat (api/views.py:1382), cleanup post-Fase-5,
    Bloque 4. Confirmado por grep exclusivo de Solicitante2022
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
