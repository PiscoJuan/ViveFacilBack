from rest_framework import status
from rest_framework.response import Response

from notifications.models import Notificacion, NotificacionMasiva
from api.serializers import NotificacionMasivaSerializer, NotificacionSerializer
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import AdminAPIView
from notifications import services


class NotificacionAnuncioAdminView(AdminAPIView):
    """Ruta base `admin/notifications/notificacion-anuncio/`
    (GET+POST+PUT+DELETE) — antes Admin2022 la pedía en
    `web/notifications/notificacion-anuncio/` (misma lógica que
    notifications.api.web.views.NotificacionAnuncioWebView; distinta de
    NotificacionAnuncioDetalleAdminView, que solo cubre `estado/`+`envio/`)."""

    def get(self, request, format=None):
        return Response(NotificacionMasivaSerializer(services.list_notificaciones_masivas(), many=True).data)

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


class NotificacionesAdminView(AdminAPIView, MyPaginationMixin):
    """Admin-exclusivo: ningún otro frontend llama `notificaciones/`."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.list_notificaciones())
        if page is not None:
            return self.get_paginated_response(NotificacionSerializer(page, many=True).data)

    def post(self, request, format=None):
        notificacion, data = services.crear_notificacion(request.data, request.FILES)
        if notificacion is not None:
            data['notificacion'] = NotificacionSerializer(notificacion).data
        return Response(data)

    def put(self, request, id, format=None):
        try:
            notificacion = services.actualizar_notificacion(id, request.data)
            serializer = NotificacionSerializer(notificacion, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Notificacion.DoesNotExist:
            return Response({"error": "Notificación no encontrada."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, id, format=None):
        success, message = services.eliminar_notificacion(id)
        return Response(
            {"success": success, "message": message},
            status=status.HTTP_200_OK if success else status.HTTP_204_NO_CONTENT,
        )


class NotificacionesDetalleAdminView(AdminAPIView):
    """Sirve `notificaciones_estado/` (PUT) y `notificaciones-envio/`
    (POST), ambas sin `pk` en la URL — el `id` viene por query param en
    ambas."""

    def put(self, request, format=None):
        services.actualizar_estado_notificacion(request.GET.get('id'), request.data.get('estado'))
        return Response(status=status.HTTP_200_OK)

    def post(self, request, format=None):
        services.enviar_notificacion_segmentada(request.GET.get('id'))
        return Response(
            {"message": "Notificación enviada correctamente a los proveedores seleccionados."},
            status=status.HTTP_200_OK,
        )


class EmailBienvenidaAdminView(AdminAPIView):
    """Confirmado exclusivo de Admin2022 (`python-anywhere.service.ts:855`)."""

    def post(self, request, format=None):
        return Response(services.enviar_email_bienvenida(
            request.data.get('email'), request.data.get('password'), request.data.get('tipo'),
        ))


class CorreoSolicitudAdminView(AdminAPIView):
    """Confirmado exclusivo de Admin2022
    (`python-anywhere.service.ts:1913`)."""

    def post(self, request, format=None):
        return Response(services.enviar_correo_solicitud(
            request.data.get('email'), request.data.get('profesion'), request.data.get('estado'),
        ))


class EnviarAlertaAdminView(AdminAPIView):
    """Confirmado exclusivo de Admin2022
    (`python-anywhere.service.ts:1363`). El original expone esto como GET
    con efecto secundario (envía un correo) — se preserva tal cual, no se
    convierte a POST."""

    def get(self, request, user_email, asunto, texto, format=None):
        return Response(services.enviar_alerta(user_email, asunto, texto))


class NotificacionGeneralAdminView(AdminAPIView):
    """Sin consumidor real confirmado en ningún frontend — se registra
    bajo `admin/` por descarte."""

    def post(self, request, format=None):
        return Response(services.notificar_general(
            request.data.get('user'), request.data.get('message'), request.data.get('title'),
        ))


class NotificacionAnuncioDetalleAdminView(AdminAPIView):
    """Sirve `notificacion-anuncio-estado/` (PUT) y
    `notificacion-anuncio-envio/` (POST), mismo patrón sin `pk` en la URL
    que NotificacionesDetalleAdminView."""

    def put(self, request, format=None):
        services.actualizar_estado_notificacion_masiva(request.GET.get('id'), request.data.get('estado'))
        return Response(status=status.HTTP_200_OK)

    def post(self, request, format=None):
        services.enviar_notificacion_masiva_segmentada(request.GET.get('id'))
        return Response(
            {"message": "Notificación enviada correctamente a los proveedores seleccionados."},
            status=status.HTTP_200_OK,
        )
