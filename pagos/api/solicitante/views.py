import logging

from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsPublic
from core.views import SolicitanteAPIView
from pagos.models import ConfiguracionPaymentez, TransaccionPaymentez
from pagos.serializers import (
    EliminarTarjetaSerializer,
    PagarSerializer,
    VerificarSerializer,
)
from pagos.services.paymentez_client import PaymentezClient, PaymentezError
from pagos.services.pago_controller import (
    PagoError,
    PagoSolicitudController,
    paymentez_uid,
)

logger = logging.getLogger("api")


def _respuesta(resultado, transaccion):
    """Cuerpo estándar para pagar/verificar."""
    return {
        "ok": resultado.ok,
        "mensaje": resultado.mensaje,
        "requiere_accion": resultado.requiere_accion,
        "transaccion_id": transaccion.id if transaccion else None,
        "estado": transaccion.estado if transaccion else None,
        "threeds": resultado.threeds or None,
    }


class ConfigClienteView(SolicitanteAPIView):
    """Expone SOLO las credenciales client (públicas) para el SDK JS.
    Las llaves server jamás salen del backend."""

    def get(self, request, format=None):
        config = ConfiguracionPaymentez.objects.filter(is_active=True).first()
        if not config:
            return Response({"error": "No hay configuración de pagos activa."}, status=503)
        return Response({
            "app_code_client": config.app_code_client,
            "app_key_client": config.app_key_client,
            "ambiente": config.ambiente,
            "url_base": config.url_base,
            "uid": paymentez_uid(request.user),
        })


class PagarView(SolicitanteAPIView):
    def post(self, request, format=None):
        serializer = PagarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            resultado, transaccion = PagoSolicitudController.procesar_pago(
                usuario=request.user,
                solicitud_id=data["solicitud_id"],
                card_token=data["datos_tarjeta"]["token"],
                card_cvc=data["datos_tarjeta"]["cvc"],
                cupon_codigo=data.get("cupon_codigo") or None,
                datos_facturacion=data.get("datos_facturacion"),
                browser_info=data.get("browser_info"),
            )
        except PagoError as exc:
            return Response({"ok": False, "mensaje": exc.mensaje}, status=exc.http_status)
        except PaymentezError as exc:
            logger.exception("Error de conexión con Paymentez")
            return Response({"ok": False, "mensaje": str(exc)}, status=502)
        return Response(_respuesta(resultado, transaccion), status=resultado.http_status)


class VerificarView(SolicitanteAPIView):
    def post(self, request, format=None):
        serializer = VerificarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            resultado, transaccion = PagoSolicitudController.verificar_transaccion(
                usuario=request.user,
                transaccion_id=data["transaccion_id"],
                value=data["value"],
                tipo=data["tipo"],
            )
        except PagoError as exc:
            return Response({"ok": False, "mensaje": exc.mensaje}, status=exc.http_status)
        except PaymentezError as exc:
            logger.exception("Error de conexión con Paymentez")
            return Response({"ok": False, "mensaje": str(exc)}, status=502)
        return Response(_respuesta(resultado, transaccion), status=resultado.http_status)


class VerificarEstadoView(SolicitanteAPIView):
    def get(self, request, transaccion_id, format=None):
        tx = TransaccionPaymentez.objects.filter(
            id=transaccion_id, usuario=request.user
        ).first()
        if not tx:
            return Response({"error": "Transacción no encontrada."}, status=404)
        return Response({
            "transaccion_id": tx.id,
            "estado": tx.estado,
            "estado_paymentez": tx.estado_paymentez,
            "status_detail": tx.status_detail,
            "monto": str(tx.monto),
            "pagada": tx.solicitud.pagada if tx.solicitud else None,
        })


class ListarTarjetasView(SolicitanteAPIView):
    def get(self, request, format=None):
        try:
            cards = PaymentezClient().list_cards(paymentez_uid(request.user))
        except PaymentezError as exc:
            return Response({"error": str(exc)}, status=502)
        return Response({"cards": cards})


class EliminarTarjetaView(SolicitanteAPIView):
    def post(self, request, format=None):
        serializer = EliminarTarjetaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            resultado = PaymentezClient().delete_card(
                serializer.validated_data["token"], paymentez_uid(request.user)
            )
        except PaymentezError as exc:
            return Response({"error": str(exc)}, status=502)
        return Response({"ok": resultado.ok, "mensaje": resultado.mensaje},
                        status=resultado.http_status)


class WebhookPaymentezView(APIView):
    """Callback servidor-a-servidor de Paymentez/Nuvei. Público, validado por
    stoken. Devuelve 203 si el stoken es inválido, 200 si se procesó."""

    permission_classes = [IsPublic]
    authentication_classes = []

    def post(self, request, format=None):
        data = request.data or {}
        tx = data.get("transaction") or {}
        user = data.get("user") or {}
        tx_id = tx.get("id")
        user_id = user.get("id")
        stoken = tx.get("stoken")

        if not PaymentezClient.stoken_valido(tx_id, user_id, stoken):
            logger.warning("Webhook Paymentez con stoken inválido: tx=%s", tx_id)
            return Response({"detail": "stoken inválido"}, status=203)

        transaccion = TransaccionPaymentez.objects.filter(id=tx_id).first()
        if not transaccion:
            logger.warning("Webhook Paymentez: transacción desconocida %s", tx_id)
            return Response({"detail": "transacción desconocida"}, status=200)

        estado_raw = tx.get("status")
        status_detail = tx.get("status_detail")
        transaccion.estado_paymentez = tx.get("current_status") or estado_raw
        transaccion.status_detail = status_detail
        transaccion.respuesta_cruda = data
        if estado_raw == "success":
            transaccion.estado = "aprobada"
            transaccion.save()
            try:
                from pagos.services.pago_controller import _finalizar
                _finalizar(transaccion)
            except Exception:
                logger.exception("Webhook: no se pudo finalizar la transacción %s", tx_id)
                return Response({"detail": "error"}, status=500)
        elif estado_raw in ("failure", "cancelled"):
            transaccion.estado = "rechazada"
            transaccion.save()
        else:
            transaccion.save()
        return Response({"detail": "ok"}, status=200)


class Paymentez3DSTermView(APIView):
    """term_url del flujo 3DS (web). Paymentez redirige/pega aquí tras el
    challenge. Público; se identifica por el ctx único de la transacción."""

    permission_classes = [IsPublic]
    authentication_classes = []

    def _procesar(self, request, ctx):
        transaccion = TransaccionPaymentez.objects.filter(threeds_ctx=ctx).first()
        if not transaccion:
            return Response({"detail": "ctx desconocido"}, status=404)
        try:
            resultado, transaccion = PagoSolicitudController.verificar_transaccion(
                usuario=transaccion.usuario,
                transaccion_id=transaccion.id,
                value="",
                tipo="BY_CRES",
            )
        except (PagoError, PaymentezError):
            logger.exception("Error resolviendo 3DS term para ctx %s", ctx)
        return Response({"detail": "ok"})

    def get(self, request, ctx, format=None):
        return self._procesar(request, ctx)

    def post(self, request, ctx, format=None):
        return self._procesar(request, ctx)
