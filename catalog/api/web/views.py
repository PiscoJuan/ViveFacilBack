from rest_framework.response import Response

from core.permissions import IsAdministrador, IsPublic
from core.views import WebAPIView
from catalog import services
from catalog.api.web.serializers import CiudadSerializer, ProfesionSerializer, ServicioSerializer


class ProfesionesWebView(WebAPIView):
    """Lectura pública; el POST/PUT que comparten esta misma URL
    (`profesiones/`) son admin-exclusivos."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsPublic()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        serializer = ProfesionSerializer(services.list_profesiones_activas(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data = services.crear_profesion(
            request.data.get("nombre"), request.data.get("descripcion"),
            request.data.get("servicio"), request.FILES.get('foto'),
        )
        return Response(data)

    def put(self, request, format=None):
        data, valido = services.actualizar_profesion(
            request.data.get("id"), request.data.get("servicio"), request.data
        )
        if not valido:
            return Response(data, status=400)
        return Response(data, status=200)


class ServiciosWebView(WebAPIView):
    """Lectura pública; el POST que comparte esta misma URL (`servicios/`)
    es admin-exclusivo."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsPublic()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        todas = request.GET.get("todas")
        serializer = ServicioSerializer(services.list_servicios(todas=bool(todas)), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        _, data = services.crear_servicio(
            request.POST.get('nombre'), request.POST.get('descripcion'),
            request.POST.get('categoria'), request.FILES.get('foto'),
        )
        return Response(data)


class CiudadesWebView(WebAPIView):
    """Lectura pública, usada por Provedor2022, Solicitante2022 y
    Admin2022 — más el POST admin-exclusivo que comparte esta misma URL
    (`ciudades/`). Admin2022 además llama un PUT a `ciudades/` que nunca
    existió en el backend (405 real) — no se inventa acá."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsPublic()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        serializer = CiudadSerializer(services.listar_ciudades(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        data, valido = services.crear_ciudad(request.data)
        if not valido:
            return Response(data, status=400)
        return Response(data, status=201)
