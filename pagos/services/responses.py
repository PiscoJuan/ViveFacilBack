"""
Interpretación de las respuestas de Paymentez.

status_detail relevantes (Nuvei/Paymentez):
    1  -> verificación adicional requerida
    3  -> aprobada
    31 -> esperando OTP
    32 -> OTP validado
    33 -> OTP no validado
    35 -> 3DS método (hidden iframe)
    36 -> 3DS challenge (iframe visible)
    37 -> rechazo durante 3DS
    48 -> 3DS completado
"""
import logging

logger = logging.getLogger("api")

# status_detail que implican que la transacción sigue su curso (no es un error)
STATUS_OTP = 31
STATUS_3DS_METHOD = 35
STATUS_3DS_CHALLENGE = 36
STATUS_APROBADA = 3
STATUS_OTP_VALIDADO = 32

PENDIENTES = {STATUS_OTP, STATUS_3DS_METHOD, STATUS_3DS_CHALLENGE}


MENSAJES_USUARIO = {
    1: "Verificación adicional requerida. Revisa los pasos de autenticación.",
    3: "Pago exitoso.",
    4: "El pago está en disputa.",
    6: "La transacción fue rechazada por sospecha de fraude.",
    7: "La transacción fue reembolsada.",
    8: "La transacción fue reversada por contracargo.",
    9: "Fondos insuficientes.",
    10: "Error en el sistema. Intenta nuevamente.",
    11: "Rechazada por controles de seguridad.",
    12: "Tarjeta no soportada.",
    14: "La transacción expiró por tiempo límite.",
    16: "Rechazada por el procesador.",
    17: "Monto excede el límite permitido.",
    18: "Cancelada por el usuario.",
    19: "Código de autorización inválido.",
    20: "Código de autorización expirado.",
    22: "Tarjeta reportada como perdida.",
    23: "Tarjeta reportada como robada.",
    24: "Tarjeta expirada.",
    25: "Tarjeta restringida.",
    31: "Esperando verificación por OTP.",
    33: "El código OTP no fue validado.",
    34: "Reembolso parcial procesado.",
    35: "Autenticación 3DS en proceso.",
    36: "Autenticación 3DS en proceso (challenge requerido).",
    37: "Rechazo durante la verificación 3DS. Intenta con otra tarjeta.",
    47: "Error de validación de los datos de la tarjeta.",
    48: "Autenticación 3DS completada.",
}


def mensaje_usuario(status_detail):
    return MENSAJES_USUARIO.get(
        status_detail,
        "No se pudo procesar la transacción. Intenta más tarde o con otro método.",
    )


class ResultadoPaymentez:
    """Resultado normalizado de una llamada a Paymentez."""

    def __init__(self, ok, data, http_status, mensaje="", requiere_accion=False,
                 threeds=None):
        self.ok = ok
        self.data = data
        self.http_status = http_status
        self.mensaje = mensaje
        self.requiere_accion = requiere_accion  # OTP o 3DS pendiente
        self.threeds = threeds or {}

    @property
    def transaction(self):
        return (self.data or {}).get("transaction", {})

    @property
    def card(self):
        return (self.data or {}).get("card", {})


def interpretar_respuesta(response, endpoint=""):
    """
    Convierte una respuesta `requests.Response` de Paymentez en un
    ResultadoPaymentez normalizado.
    """
    try:
        data = response.json()
    except ValueError:
        logger.error("Respuesta no JSON de Paymentez en %s: %s", endpoint, response.text)
        return ResultadoPaymentez(
            ok=False,
            data={"error": "Respuesta inválida del proveedor de pagos."},
            http_status=502,
            mensaje="Error inesperado del proveedor de pagos. Intenta nuevamente.",
        )

    logger.debug("Paymentez[%s] -> %s", endpoint, data)

    # --- eliminación de tarjeta ---
    if endpoint == "delete_card":
        error = data.get("error")
        if not error and data.get("message") == "card deleted":
            return ResultadoPaymentez(True, {"message": "Tarjeta eliminada"}, 200,
                                      "Tarjeta eliminada correctamente")
        msg = (error or {}).get("help") or data.get("message") or "No se pudo eliminar la tarjeta"
        return ResultadoPaymentez(False, {"error": msg}, 400, msg)

    if response.status_code != 200:
        logger.warning("HTTP %s de Paymentez en %s: %s", response.status_code, endpoint, data)
        return ResultadoPaymentez(
            ok=False,
            data={"error": "No se pudo procesar la transacción.", "details": data},
            http_status=response.status_code,
            mensaje="No se pudo procesar la transacción. Intenta nuevamente.",
        )

    transaction = data.get("transaction", {})
    status_detail = transaction.get("status_detail")

    # 3DS pendiente (method o challenge)
    if status_detail in (STATUS_3DS_METHOD, STATUS_3DS_CHALLENGE):
        threeds_data = data.get("3ds", {})
        browser_response = threeds_data.get("browser_response", {})
        return ResultadoPaymentez(
            ok=True,
            data=data,
            http_status=202,
            mensaje=mensaje_usuario(status_detail),
            requiere_accion=True,
            threeds={
                "status_detail": status_detail,
                "hidden_iframe": browser_response.get("hidden_iframe"),
                "challenge_request": browser_response.get("challenge_request"),
            },
        )

    estado = transaction.get("status")
    if estado not in ("success", "pending"):
        detail = transaction.get("status_detail")
        logger.warning("Transacción fallida en %s | detalle %s | data %s", endpoint, detail, data)
        return ResultadoPaymentez(
            ok=False,
            data={"error": mensaje_usuario(detail)},
            http_status=402,  # Payment Required: rechazo del medio de pago
            mensaje=mensaje_usuario(detail),
        )

    if estado == "pending":
        # OTP u otra verificación pendiente
        return ResultadoPaymentez(
            ok=True,
            data=data,
            http_status=202,
            mensaje=mensaje_usuario(status_detail),
            requiere_accion=True,
        )

    return ResultadoPaymentez(True, data, 200, mensaje_usuario(status_detail))
