from rest_framework.response import Response

from core.views import WebAPIView
from promotions import services


class ConfirmarDescuentoWebView(WebAPIView):
    """Replica de ConfirmarDescuento (api/views.py:6235). Devuelve un string
    plano ("descuento"/"reclamado"/"usado"/"no_existe") — mantener ese
    formato, el frontend lo compara directo, no envolver en un dict."""

    def get(self, request, mail, format=None):
        return Response(services.confirmar_descuento(mail))
