from django.http import HttpResponse
from rest_framework.response import Response

from api.serializers import PoliticasSerializer
from content import services
from core.views import WebAPIView



class PoliticasWebView(WebAPIView):
    """Lectura pública de `Politics` (api/views.py:5322). Solo el GET —
    la ruta vieja `politics/` sigue viva sin tocar, sigue manejando además
    POST/PUT (gestión), que se migran recién en la Fase 5. Registrada bajo
    `web/` (no `solicitante/`) porque tanto ViveFacil_Solicitante2022 como
    ViveFacil_Provedor2022 la consultan — ver
    docs/refactor/05-fase-3-solicitante.md#nota-politics-es-multi-rol."""

    def get(self, request, format=None):
        serializer = PoliticasSerializer(services.list_politicas(), many=True)
        return Response(serializer.data)


class TerminosCondicionesWebView(WebAPIView):
    """Réplica exacta de Politica.get (api/views.py:2024-2026), cleanup
    post-Fase-5, Bloque 4. Texto estático hardcodeado (no depende de
    `Politicas` en base de datos, a diferencia de `PoliticasWebView` /
    `politics/` — son endpoints genuinamente distintos pese al nombre
    parecido). Confirmado por grep fresco: sin consumidor real en ningún
    frontend (ninguno llama `politica/` en singular); se migra igual por
    consistencia. Devuelve texto plano, no JSON, tal cual el original
    (`HttpResponse`, no `Response` de DRF)."""

    def get(self, request, format=None):
        return HttpResponse(services.terminos_condiciones_texto())
