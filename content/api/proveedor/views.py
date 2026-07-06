from rest_framework.response import Response

from api.serializers import InsigniaSerializer, MedallaSerializer
from content import services
from core.views import ProveedorAPIView


class InsigniasProveedorView(ProveedorAPIView):
    """Réplica de InsigniasProveedor (api/views.py:490). Antes sin ningún
    permission_classes (abierto); la ruta nueva exige IsProveedor."""

    def get(self, request, format=None):
        return Response(InsigniaSerializer(services.list_insignias_proveedor(), many=True).data)


class InsigniasPersonalesProveedorView(ProveedorAPIView):
    """Réplica de InsigniasPersonales.get (api/views.py:237), endpoint
    multi-rol (ver `content.api.solicitante.views.InsigniasPersonalesSolicitanteView`),
    cleanup post-Fase-5, Bloque 4."""

    def get(self, request, id, format=None):
        return Response(InsigniaSerializer(services.insignias_personales(id), many=True).data)


class MedallasPersonalesProveedorView(ProveedorAPIView):
    """Réplica de MedallasPersonales.get (api/views.py:313), endpoint
    multi-rol (ver `content.api.solicitante.views.MedallasPersonalesSolicitanteView`),
    cleanup post-Fase-5, Bloque 4."""

    def get(self, request, format=None):
        return Response(MedallaSerializer(services.medallas_personales(request.user), many=True).data)


class SugerenciasProveedorView(ProveedorAPIView):
    """Réplica del POST de Suggestions (api/views.py:1810), endpoint
    multi-rol (ver `content.api.solicitante.views.SugerenciasSolicitanteView`),
    cleanup post-Fase-5, Bloque 4."""

    def post(self, request, format=None):
        return Response(services.crear_sugerencia(request.POST, request.FILES))
