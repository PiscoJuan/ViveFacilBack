from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import SolicitudSerializer
from solicitudes import services


class SolicitudWebView(APIView):
    """Endpoint compartido por proveedor y solicitante (`solicitud/`,
    `solicitud/<id>`); cada rol también tiene su propia vista en su
    namespace (`SolicitudSolicitanteView` / `SolicitudProveedorView`).
    Mantiene `IsAuthenticated` genérico en vez de restringir a un rol, para
    no romper al otro mientras ambos sigan llamando esta ruta."""

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        return Response(services.listar_todas_solicitudes())

    def put(self, request, solicitud_ID, format=None):
        data, http_status = services.actualizar_solicitud(solicitud_ID, request.data)
        return Response(data, status=http_status)


class AddSolicitudWebView(APIView):
    """Endpoint compartido por solicitante y proveedor (`crear/` en ambos
    namespaces). Mantiene `IsAuthenticated` genérico en vez de restringir a
    un rol."""

    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        solicitud, data = services.crear_solicitud(request.data, request.FILES)
        if solicitud is not None:
            data['solicitud'] = SolicitudSerializer(solicitud).data
        return Response(data)


class HistorialSolicitudesWebView(APIView):
    """Endpoint compartido por solicitante y proveedor
    (`solicitudes/<user>`); cada rol también tiene su propia vista
    (`HistorialSolicitudesSolicitanteView`/`HistorialSolicitudesProveedorView`).
    Sin `permission_classes` a propósito, no restringir a un rol sin
    verificar que el otro ya migró."""

    def get(self, request, user, format=None):
        return Response(services.historial_solicitudes_por_email(user))


class SolicitudAdjudicadaWebView(APIView):
    """Endpoint compartido por solicitante y proveedor; cada rol también
    tiene su propia vista. Sin `permission_classes` a propósito."""

    def get(self, request, solicitud_ID, format=None):
        return Response(services.solicitud_adjudicada(solicitud_ID))
