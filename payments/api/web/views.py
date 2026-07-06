from rest_framework.response import Response

from core.views import WebAPIView
from payments import services
from payments.api.web.serializers import BancoSerializer


class BancosWebView(WebAPIView):
    """Lectura pública de `Bancos` (api/views.py:6335), que ya separaba GET
    público de POST/DELETE autenticados con `get_permissions()`. La ruta
    vieja `bancos/` sigue viva sin tocar — su POST/DELETE se migran en la
    Fase 5 (admin)."""

    def get(self, request, format=None):
        serializer = BancoSerializer(services.list_bancos(), many=True)
        return Response(serializer.data)
