from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import InsigniaSerializer, MedallaSerializer, PoliticasSerializer
from content import services
from core.permissions import IsAdministrador, IsPublic
from core.views import WebAPIView



class PoliticasWebView(WebAPIView):
    """GET público, consumido por ViveFacil_Solicitante2022,
    ViveFacil_Provedor2022 y ViveFacil_Admin2022. PUT (edición, por
    `identifier`) solo en Admin2022 (`politicas.component.ts::saveChanges`).
    POST sin consumidor real confirmado en ningún frontend."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsPublic()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        serializer = PoliticasSerializer(services.list_politicas(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        politica, _ = services.crear_o_actualizar_politica(
            request.data.get('identifier'), request.data.get('terminos'))
        return Response({'politics': PoliticasSerializer(politica).data})

    def put(self, request, identifier, format=None):
        from django.core.exceptions import ObjectDoesNotExist

        try:
            politica = services.actualizar_politica(identifier, request.data.get('terminos'))
        except ObjectDoesNotExist:
            return Response({"error": "Política no encontrada."}, status=404)
        return Response({'politics': PoliticasSerializer(politica).data})


class SugerenciasWebView(WebAPIView):
    """GET sin consumidor real confirmado en ningún frontend. El POST ya
    tiene home propio por rol (`SugerenciasProveedorView`/
    `SugerenciasSolicitanteView`) — ambos frontends migrados a esos paths;
    esta ruta legacy solo queda como red de seguridad para versiones viejas
    de la app móvil, sin permiso reforzado (nunca declaró
    `permission_classes`, queda abierta por default de DRF)."""

    def get(self, request, format=None):
        from api.serializers import SuggestionSerializer

        return Response(SuggestionSerializer(services.list_sugerencias(), many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_sugerencia(request.POST, request.FILES))


class InsigniasPersonalesWebView(WebAPIView):
    """GET público (nunca declaró `permission_classes`, default DRF es
    `AllowAny`, igual que `WebAPIView`) — Provedor2022 es el único
    consumidor real confirmado."""

    def get(self, request, id, format=None):
        serializer = InsigniaSerializer(services.insignias_personales(id), many=True)
        return Response(serializer.data)


class MedallasPersonalesWebView(APIView):
    """Preserva `IsAuthenticated` genérico (cualquier rol logueado, no
    `IsPublic` como las demás vistas de este archivo). Solicitante2022 es
    el único consumidor real confirmado."""

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        serializer = MedallaSerializer(services.medallas_personales(request.user), many=True)
        return Response(serializer.data)


class InsigniasWebView(WebAPIView):
    """Su PUT/DELETE viven en
    `content.api.admin.views.InsigniasAdminView` (nunca hubo URL real que
    los sirviera desde acá). GET compartido de verdad con Provedor2022 y
    Solicitante2022; POST admin-exclusivo."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsPublic()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        from content.models import Insignia

        serializer = InsigniaSerializer(Insignia.objects.all().filter(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        return Response(services.crear_insignia(request.POST, request.FILES))


class TerminosCondicionesWebView(WebAPIView):
    """Texto estático hardcodeado (no depende de `Politicas` en base de
    datos, a diferencia de `PoliticasWebView` / `politics/` — son
    endpoints genuinamente distintos pese al nombre parecido). Sin
    consumidor real confirmado en ningún frontend. Devuelve texto plano,
    no JSON (`HttpResponse`, no `Response` de DRF)."""

    def get(self, request, format=None):
        return HttpResponse(services.terminos_condiciones_texto())
