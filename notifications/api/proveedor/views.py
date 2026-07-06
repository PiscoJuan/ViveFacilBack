from rest_framework.response import Response

from core.views import ProveedorAPIView
from notifications import services


class NotificacionChatProveedorView(ProveedorAPIView):
    """Réplica de Notificacion_Chat_Proveedor (api/views.py:3118). Antes sin
    ningún permission_classes (abierto); la ruta nueva exige IsProveedor.
    Primera vez que se usa la app `notifications` (Fase 3 había resuelto
    `DeviceNotification`/`post-token` dentro de `accounts.services` por ser
    puro CRUD sobre el modelo de `fcm_django`; esto en cambio es lógica de
    dominio propia — chat — así que sí amerita vivir acá)."""

    def post(self, request, format=None):
        data, http_status = services.notificar_chat_proveedor(
            request.data.get("remitente"),
            request.data.get("user"),
            request.data.get("message"),
            request.data.get("url"),
        )
        return Response(data, status=http_status)
