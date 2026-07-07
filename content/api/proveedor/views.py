from rest_framework.response import Response

from api.serializers import InsigniaSerializer, MedallaSerializer, PoliticasSerializer
from content import services
from core.views import ProveedorAPIView


class PoliticasProveedorView(ProveedorAPIView):
    """Endpoint propio del proveedor para políticas — antes pedía directo
    a `web/content/politicas/` (content.api.web.views.PoliticasWebView)."""

    def get(self, request, format=None):
        return Response(PoliticasSerializer(services.list_politicas(), many=True).data)


class InsigniasProveedorView(ProveedorAPIView):
    def get(self, request, format=None):
        return Response(InsigniaSerializer(services.list_insignias_proveedor(), many=True).data)


class InsigniasPersonalesProveedorView(ProveedorAPIView):
    """Endpoint compartido con Solicitante (ver
    `content.api.solicitante.views.InsigniasPersonalesSolicitanteView`)."""

    def get(self, request, id, format=None):
        return Response(InsigniaSerializer(services.insignias_personales(id), many=True).data)


class MedallasPersonalesProveedorView(ProveedorAPIView):
    """Endpoint compartido con Solicitante (ver
    `content.api.solicitante.views.MedallasPersonalesSolicitanteView`)."""

    def get(self, request, format=None):
        return Response(MedallaSerializer(services.medallas_personales(request.user), many=True).data)


class SugerenciasProveedorView(ProveedorAPIView):
    """Endpoint compartido con Solicitante (ver
    `content.api.solicitante.views.SugerenciasSolicitanteView`)."""

    def post(self, request, format=None):
        return Response(services.crear_sugerencia(request.POST, request.FILES))
