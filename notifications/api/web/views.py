from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.models import NotificacionMasiva
from api.serializers import NotificacionMasivaSerializer
from core.permissions import IsAdministrador
from core.views import WebAPIView
from notifications import services


class NotificacionAnuncioWebView(WebAPIView):
    """GET compartido de verdad con Provedor2022 y Solicitante2022 — no
    puede registrarse bajo `admin/` sin duplicar la URL que ya usan los
    otros dos roles. POST/PUT/DELETE admin-only (el método análogo del
    lado proveedor, `postNotificacionMasiva`, existe en el frontend pero
    ningún componente lo invoca — código muerto, no hay un segundo emisor
    real)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdministrador()]

    def get(self, request, format=None):
        serializer = NotificacionMasivaSerializer(services.list_notificaciones_masivas(), many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        notificacion, data = services.crear_notificacion_masiva(request.data, request.FILES)
        if notificacion is not None:
            data['notificacion_masiva'] = NotificacionMasivaSerializer(notificacion).data
        return Response(data)

    def put(self, request, id, format=None):
        try:
            notificacion = services.actualizar_notificacion_masiva(id, request.data)
            serializer = NotificacionMasivaSerializer(notificacion, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except NotificacionMasiva.DoesNotExist:
            return Response({"error": "Notificación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id):
        success, message = services.eliminar_notificacion_masiva(id)
        return Response({"success": success, "message": message})
