from rest_framework.response import Response

from api.serializers import Profesion_ProveedorSerializer
from catalog import services
from core.views import SolicitanteAPIView


class ProveedoresPorServicioSolicitanteView(SolicitanteAPIView):
    """Réplica de ProveedoresByProfesion (api/views.py:2482)."""

    def get(self, request, servicio_id, format=None):
        serializer = Profesion_ProveedorSerializer(
            services.proveedores_activos_por_servicio(servicio_id), many=True
        )
        return Response(serializer.data)
