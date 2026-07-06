from rest_framework.response import Response

from core.views import WebAPIView
from catalog import services
from catalog.api.web.serializers import ProfesionSerializer, ServicioSerializer


class ProfesionesWebView(WebAPIView):
    """Lectura pública de `Profesiones` (api/views.py:2536). La ruta vieja
    `profesiones/` sigue viva y sin tocar — sigue manejando además
    POST/PUT/DELETE (admin), que se migran recién en la Fase 5. Ver
    docs/refactor/01-arquitectura-objetivo.md#endpoints-con-permiso-distinto-por-verbo-http."""

    def get(self, request, format=None):
        serializer = ProfesionSerializer(services.list_profesiones_activas(), many=True)
        return Response(serializer.data)


class ServiciosWebView(WebAPIView):
    """Lectura pública de `Servicios` (api/views.py:947). Misma nota que
    ProfesionesWebView: la ruta vieja `servicios/` sigue viva sin tocar."""

    def get(self, request, format=None):
        todas = request.GET.get("todas")
        serializer = ServicioSerializer(services.list_servicios(todas=bool(todas)), many=True)
        return Response(serializer.data)
