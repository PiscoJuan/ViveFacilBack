from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import TarjetaSerializer
from core.permissions import IsAdministrador, IsPublic
from core.views import WebAPIView
from payments import services
from payments.api.web.serializers import BancoSerializer


class BancosWebView(WebAPIView):
    """Lectura pública; el POST/DELETE que comparten estas mismas URLs
    (`bancos/`, `bancos/delete/<id>`) son admin-exclusivos, sin ningún
    consumidor real confirmado. Antes exigían solo `IsAuthenticated`
    (cualquier rol logueado), ahora `IsAdministrador`."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsPublic()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        serializer = BancoSerializer(services.list_bancos(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        nombre = request.data.get('nombre')
        estado = request.data.get('estado')
        if not nombre or not estado:
            return Response({'error': 'Nombre y estado son requeridos'}, status=status.HTTP_400_BAD_REQUEST)
        banco = services.crear_banco(nombre, estado)
        return Response({'id': banco.id, 'nombre': banco.nombre, 'estado': banco.estado}, status=status.HTTP_201_CREATED)

    def delete(self, request, id, format=None):
        from api.models import Banco

        try:
            services.eliminar_banco(id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Banco.DoesNotExist:
            return Response({'error': 'Banco no encontrado'}, status=status.HTTP_404_NOT_FOUND)


class TarjetaWebView(APIView):
    """Preserva el mismo `IsAuthenticated` genérico (cualquier rol
    logueado). `GET` (lista TODAS las tarjetas sin filtrar) sin llamador
    real confirmado; `POST` (crear tarjeta) ya tiene home real por rol
    (`payments.api.solicitante.views.TarjetaSolicitanteView`) — esta ruta
    legacy queda como red de seguridad."""

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        return Response(TarjetaSerializer(services.list_tarjetas_todas(), many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_tarjeta(request.data))


class TarjetaUserWebView(APIView):
    """Preserva el mismo `IsAuthenticated` genérico. GET multi-rol
    (Solicitante2022 + Provedor2022 lectura, ya con home propio por rol);
    DELETE exclusivo de Solicitante2022
    (`payments.api.solicitante.views.TarjetaSolicitanteView`). Esta ruta
    legacy queda como red de seguridad para versiones viejas."""

    permission_classes = [IsAuthenticated]

    def get(self, request, identifier, format=None):
        tarjetas = services.list_tarjetas_por_usuario(identifier)
        return Response(TarjetaSerializer(tarjetas, many=True).data)

    def delete(self, request, identifier, format=None):
        return Response(services.eliminar_tarjeta(identifier))
