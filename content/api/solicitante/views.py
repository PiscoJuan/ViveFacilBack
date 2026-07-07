from rest_framework.response import Response

from api.serializers import InsigniaSerializer, MedallaSerializer, PoliticasSerializer
from content import services
from core.views import SolicitanteAPIView


class PoliticasSolicitanteView(SolicitanteAPIView):
    """Endpoint propio del solicitante para políticas — antes pedía directo
    a `web/content/politicas/` (content.api.web.views.PoliticasWebView)."""

    def get(self, request, format=None):
        return Response(PoliticasSerializer(services.list_politicas(), many=True).data)


class InsigniasPersonalesSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (Solicitante2022 y Provedor2022
    llaman el mismo path legacy `insigniaspersonales/<id>`)."""

    def get(self, request, id, format=None):
        return Response(InsigniaSerializer(services.insignias_personales(id), many=True).data)


class MedallasPersonalesSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (Solicitante2022 y Provedor2022)."""

    def get(self, request, format=None):
        return Response(MedallaSerializer(services.medallas_personales(request.user), many=True).data)


class InsigniasSolicitanteView(SolicitanteAPIView):
    """Sin consumidor real confirmado en ningún frontend."""

    def get(self, request, format=None):
        return Response(InsigniaSerializer(services.list_insignias_solicitante(), many=True).data)


class SugerenciasSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor: Solicitante2022 y Provedor2022
    crean sugerencias desde `ayuda.page.ts`. El GET de la misma clase legacy
    no tiene consumidor real en ningún frontend."""

    def post(self, request, format=None):
        return Response(services.crear_sugerencia(request.POST, request.FILES))
