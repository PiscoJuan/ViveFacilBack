from rest_framework.response import Response

from api.serializers import InsigniaSerializer, MedallaSerializer
from content import services
from core.views import SolicitanteAPIView


class InsigniasPersonalesSolicitanteView(SolicitanteAPIView):
    """Réplica de InsigniasPersonales.get (api/views.py:237), endpoint
    multi-rol confirmado por grep (Solicitante2022 y Provedor2022 llaman el
    mismo path legacy `insigniaspersonales/<id>`), cleanup post-Fase-5,
    Bloque 4. Antes sin ningún permission_classes (abierto)."""

    def get(self, request, id, format=None):
        return Response(InsigniaSerializer(services.insignias_personales(id), many=True).data)


class MedallasPersonalesSolicitanteView(SolicitanteAPIView):
    """Réplica de MedallasPersonales.get (api/views.py:313), endpoint
    multi-rol confirmado por grep (Solicitante2022 y Provedor2022),
    cleanup post-Fase-5, Bloque 4. Antes exigía solo IsAuthenticated
    genérico; ahora exige IsSolicitante."""

    def get(self, request, format=None):
        return Response(MedallaSerializer(services.medallas_personales(request.user), many=True).data)


class InsigniasSolicitanteView(SolicitanteAPIView):
    """Réplica de InsigniaSolicitantes.get (api/views.py:416), cleanup
    post-Fase-5, Bloque 4. Sin evidencia de consumidor real en ningún
    frontend (grep fresco, cero resultados) — se migra igual por
    consistencia."""

    def get(self, request, format=None):
        return Response(InsigniaSerializer(services.list_insignias_solicitante(), many=True).data)


class SugerenciasSolicitanteView(SolicitanteAPIView):
    """Réplica del POST de Suggestions (api/views.py:1810), endpoint
    multi-rol confirmado (Solicitante2022 y Provedor2022 crean sugerencias
    desde `ayuda.page.ts`; el GET de la misma clase no tiene consumidor
    real en ningún frontend — confirmado por grep, queda sin tocar en
    `api/views.py`), cleanup post-Fase-5, Bloque 4."""

    def post(self, request, format=None):
        return Response(services.crear_sugerencia(request.POST, request.FILES))
