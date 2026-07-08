"""
Orquestación del cobro de una Solicitud con Paymentez, del lado del servidor.

Reglas clave (a diferencia de la implementación vieja que cobraba en el front):
  - El MONTO se calcula en el servidor desde la oferta adjudicada
    (Envio_Interesados.oferta) y un descuento validado en la BD. Nunca se
    confía en un monto enviado por el cliente.
  - El CVC llega en el request y solo se pasa a Paymentez; nunca se guarda.
  - El registro contable (PagoTarjeta + PagoSolicitud) se crea SOLO cuando el
    pago queda aprobado. OTP/3DS pendiente deja la transacción en 'pendiente'.
"""
import logging
import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from pagos.models import EstadoTransaccion, TransaccionPaymentez
from pagos.services.paymentez_client import PaymentezClient
from pagos.services.responses import ResultadoPaymentez

logger = logging.getLogger("api")

CENT = Decimal("0.01")
TAX_PCT = Decimal("15")  # IVA Ecuador
TAX_FACTOR = Decimal("1.15")


class PagoError(Exception):
    """Error de negocio con un http_status asociado."""

    def __init__(self, mensaje, http_status=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.http_status = http_status


# --------------------------------------------------------------------- helpers
def paymentez_uid(user):
    # La app históricamente usó el username como uid de Paymentez (y las
    # tarjetas guardadas quedaron tokenizadas bajo ese uid). Se mantiene para
    # no huérfanar tarjetas existentes. ponytail: si algún día se normaliza,
    # migrar los tokens antes de cambiar esto.
    return user.username


def _email(user):
    return user.email or user.username


def _oferta_adjudicada(solicitud) -> Decimal:
    """Monto base = la oferta del proveedor adjudicado (interesado=True)."""
    from solicitudes.models import Envio_Interesados

    ei = (
        Envio_Interesados.objects
        .filter(solicitud=solicitud, interesado=True)
        .order_by("-fecha_creacion")
        .first()
    )
    if not ei or ei.oferta is None:
        raise PagoError("La solicitud no tiene una oferta adjudicada.", 409)
    return Decimal(str(ei.oferta))


def _descuento_pct(username, user, cupon_codigo):
    """
    Descuento validado server-side. Devuelve (porcentaje:int, cupon|None,
    usar_descuento_unico:bool). Prioridad: cupón válido > descuento único.
    """
    from django.utils import timezone

    from promotions.models import Cupon, Cupon_Aplicado
    from promotions.services import revisar_descuento_unico

    if cupon_codigo:
        try:
            cupon = Cupon.objects.get(codigo=cupon_codigo, estado=True)
        except Cupon.DoesNotExist:
            raise PagoError("El cupón no existe o no está activo.", 400)
        ahora = timezone.now()
        if not (cupon.fecha_iniciacion <= ahora <= cupon.fecha_expiracion):
            raise PagoError("El cupón está fuera de su periodo de validez.", 400)
        disponible = Cupon_Aplicado.objects.filter(
            cupon=cupon, user=username, estado=True
        ).exists()
        if not disponible:
            raise PagoError("El cupón no está disponible para este usuario.", 400)
        pct = max(0, min(100, int(cupon.porcentaje)))
        return pct, cupon, False

    if revisar_descuento_unico(user) == "descuento":
        return 15, None, True

    return 0, None, False


def _montos(oferta: Decimal, pct: int) -> dict:
    """
    Replica el monto que cobraba el front: `amount` = oferta con el descuento
    aplicado, tratado como IVA incluido.
    ponytail: el front viejo COBRABA este `amount` pero REGISTRABA amount*1.15
    (bug de math en cliente). Acá se cobra y se registra el MISMO `amount`.
    """
    base = (oferta * (Decimal(100 - pct) / Decimal(100)))
    amount = base.quantize(CENT, rounding=ROUND_HALF_UP)
    taxable = (amount / TAX_FACTOR).quantize(CENT, rounding=ROUND_HALF_UP)
    vat = (amount - taxable).quantize(CENT, rounding=ROUND_HALF_UP)
    return {
        "amount": amount,
        "taxable_amount": taxable,
        "vat": vat,
        "tax_percentage": TAX_PCT,
    }


def _cargo_pct(tipo) -> Decimal:
    """% configurado en content.Cargo para ese tipo (0 si no hay ninguno activo)."""
    from content.models import Cargo

    cargo = Cargo.objects.filter(tipo=tipo).first()
    return Decimal(str(cargo.porcentaje)) if cargo else Decimal("0")


def _cargos(monto: Decimal) -> dict:
    """
    Comisiones que se descuentan del pago al proveedor (el cliente sigue
    pagando `monto` completo a la tarjeta). Cada tipo (banco/paymentez/
    sistema) tiene a lo sumo un Cargo activo (unique=True en el modelo).
    """
    from content.models import TipoCargo

    resultado = {}
    for campo, tipo in (
        ("cargo_paymentez", TipoCargo.PAYMENTEZ),
        ("cargo_banco", TipoCargo.BANCO),
        ("cargo_sistema", TipoCargo.SISTEMA),
    ):
        pct = _cargo_pct(tipo)
        resultado[campo] = float((monto * pct / Decimal("100")).quantize(CENT, rounding=ROUND_HALF_UP))
    return resultado


def _estado_desde_resultado(resultado: ResultadoPaymentez) -> str:
    if not resultado.ok:
        return EstadoTransaccion.RECHAZADA
    if resultado.requiere_accion:
        return EstadoTransaccion.PENDIENTE
    return EstadoTransaccion.APROBADA


def _guardar_transaccion(*, tx_id, usuario, solicitud, montos, card_token,
                         resultado, threeds_ctx, datos_facturacion):
    tx = resultado.transaction
    card = resultado.card
    estado = _estado_desde_resultado(resultado)
    obj, _ = TransaccionPaymentez.objects.update_or_create(
        id=tx_id,
        defaults=dict(
            usuario=usuario,
            solicitud=solicitud,
            monto=montos["amount"],
            card_token=card_token or card.get("token"),
            referencia=card.get("transaction_reference") or tx.get("id"),
            codigo_autorizacion=tx.get("authorization_code"),
            referencia_dev=tx.get("dev_reference"),
            tipo_tarjeta=card.get("type"),
            bin=card.get("bin"),
            estado=estado,
            estado_paymentez=tx.get("current_status") or tx.get("status"),
            status_detail=tx.get("status_detail"),
            threeds_ctx=threeds_ctx,
            threeds_data=resultado.threeds or None,
            respuesta_cruda=resultado.data,
            datos_facturacion=datos_facturacion,
        ),
    )
    return obj


# ------------------------------------------------------------------ finalizar
def _finalizar(transaccion):
    """
    Crea PagoTarjeta + PagoSolicitud, marca la solicitud como pagada, consume
    el descuento y notifica. Idempotente respecto a la transacción (si ya tiene
    pago_tarjeta, no duplica). El descuento aplicado se lee del contexto que se
    guardó en datos_facturacion["__pago_ctx"] al momento del débito, para que
    los pagos aprobados de forma asíncrona (OTP/3DS/webhook) también lo consuman.
    """
    from payments.models import PagoSolicitud, PagoTarjeta
    from promotions.models import Cupon, Cupon_Aplicado
    from promotions.services import usar_descuento_unico

    if transaccion.pago_tarjeta_id:
        return transaccion.pago_tarjeta

    solicitud = transaccion.solicitud
    usuario = transaccion.usuario
    facturacion = transaccion.datos_facturacion or {}
    ctx = facturacion.get("__pago_ctx") or {}
    cupon = None
    if ctx.get("cupon_id"):
        cupon = Cupon.objects.filter(id=ctx["cupon_id"]).first()

    with transaction.atomic():
        pago_tarjeta = PagoTarjeta.objects.create(
            user=usuario,
            tarjeta=None,  # las tarjetas viven en Paymentez, no en la BD local
            promocion=None,
            cupon=cupon,
            valor=float(transaccion.monto),
            descripcion=facturacion.get("descripcion") or "Solicitud",
            impuesto=int(TAX_PCT),
            solicitud=solicitud,
            referencia=transaccion.referencia or transaccion.id,
            carrier_id=transaccion.codigo_autorizacion or "",
            usuario=usuario.get_full_name() or usuario.username,
            servicio=getattr(getattr(solicitud, "servicio", None), "nombre", "") or "",
            **_cargos(transaccion.monto),
        )
        PagoSolicitud.objects.create(pago_tarjeta=pago_tarjeta, solicitud=solicitud)

        transaccion.pago_tarjeta = pago_tarjeta
        transaccion.estado = EstadoTransaccion.APROBADA
        transaccion.save(update_fields=["pago_tarjeta", "estado", "fecha_actualizacion"])

        # marca la solicitud como pagada
        solicitud.pagada = True
        solicitud.termino = "pagado"
        solicitud.save(update_fields=["pagada", "termino"])

        # consumir descuento
        if cupon:
            Cupon_Aplicado.objects.filter(
                cupon=cupon, user=usuario.username, estado=True
            ).update(estado=False)
        if ctx.get("usar_desc_unico"):
            usar_descuento_unico(_email(usuario))

    _notificar_proveedor(solicitud)
    return pago_tarjeta


def _notificar_proveedor(solicitud):
    try:
        from fcm_django.models import FCMDevice

        from core.firebase import send_notificationF

        servicio = getattr(getattr(solicitud, "servicio", None), "nombre", "") or "el servicio"
        prov_user = solicitud.proveedor.user_datos.user
        devices = FCMDevice.objects.filter(active=True, user__id=prov_user.id)
        tokens = list(devices.values_list("registration_id", flat=True))
        if tokens:
            send_notificationF(
                tokens,
                "Servicio pagado: " + servicio,
                "¡Dale un vistazo!",
                {"ruta": "/historial",
                 "descripcion": f"El pago por el servicio de {servicio} fue exitoso"},
            )
    except Exception:
        logger.exception("No se pudo notificar al proveedor del pago")


# --------------------------------------------------------------------- público
class PagoSolicitudController:
    """Orquesta el cobro de una Solicitud."""

    @staticmethod
    def procesar_pago(*, usuario, solicitud_id, card_token, card_cvc,
                      cupon_codigo=None, datos_facturacion=None, browser_info=None):
        from solicitudes.models import Solicitud

        if not card_token or not card_cvc:
            raise PagoError("Faltan los datos de la tarjeta (token y cvc).", 400)

        with transaction.atomic():
            try:
                solicitud = (
                    Solicitud.objects.select_for_update()
                    .select_related("solicitante__user_datos__user")
                    .get(id=solicitud_id)
                )
            except Solicitud.DoesNotExist:
                raise PagoError("La solicitud no existe.", 404)

            if solicitud.solicitante.user_datos.user_id != usuario.id:
                raise PagoError("La solicitud no pertenece al usuario.", 403)
            if solicitud.pagada:
                raise PagoError("La solicitud ya fue pagada.", 409)
            if not solicitud.adjudicar or solicitud.proveedor_id is None:
                raise PagoError("La solicitud no está adjudicada.", 409)

            # evita doble cobro concurrente / reintento con pago en curso
            en_curso = TransaccionPaymentez.objects.filter(
                solicitud=solicitud,
                estado__in=[EstadoTransaccion.PENDIENTE, EstadoTransaccion.APROBADA],
            ).exists()
            if en_curso:
                raise PagoError("Ya hay un pago en curso o aprobado para esta solicitud.", 409)

            oferta = _oferta_adjudicada(solicitud)
            pct, cupon, usar_desc = _descuento_pct(usuario.username, usuario, cupon_codigo)
            montos = _montos(oferta, pct)

        # el contexto del descuento se guarda en la transacción para poder
        # consumirlo también cuando el pago se aprueba de forma asíncrona.
        datos_facturacion = {
            **(datos_facturacion or {}),
            "__pago_ctx": {
                "cupon_id": cupon.id if cupon else None,
                "usar_desc_unico": usar_desc,
            },
        }

        threeds_ctx = uuid.uuid4().hex
        dev_reference = f"VIVEFACIL-{threeds_ctx[:12].upper()}"

        client = PaymentezClient()
        payload = client.build_payload_debit(
            user_id=paymentez_uid(usuario),
            email=_email(usuario),
            monto=montos["amount"],
            descripcion=(datos_facturacion or {}).get("descripcion") or f"Solicitud {solicitud.id}",
            dev_reference=dev_reference,
            card_token=card_token,
            card_cvc=card_cvc,
            browser_info=browser_info,
            threeds_ctx=threeds_ctx if browser_info else None,
            vat=montos["vat"],
            taxable_amount=montos["taxable_amount"],
            tax_percentage=montos["tax_percentage"],
        )
        resultado = client.debit(payload)

        tx = resultado.transaction
        tx_id = tx.get("id")
        if not tx_id:
            # rechazo sin id de transacción: no hay nada que persistir por PK
            logger.warning("Debit sin transaction.id | %s", resultado.data)
            raise PagoError(resultado.mensaje or "El pago fue rechazado.",
                            resultado.http_status or 402)

        transaccion = _guardar_transaccion(
            tx_id=tx_id, usuario=usuario, solicitud=solicitud, montos=montos,
            card_token=card_token, resultado=resultado, threeds_ctx=threeds_ctx,
            datos_facturacion=datos_facturacion,
        )

        if resultado.ok and not resultado.requiere_accion:
            _finalizar(transaccion)

        return resultado, transaccion

    @staticmethod
    def verificar_transaccion(*, usuario, transaccion_id, value, tipo="BY_OTP"):
        """Valida OTP/3DS y finaliza el pago si la verificación aprueba."""
        try:
            transaccion = TransaccionPaymentez.objects.get(
                id=transaccion_id, usuario=usuario
            )
        except TransaccionPaymentez.DoesNotExist:
            raise PagoError("La transacción no existe.", 404)

        client = PaymentezClient()
        resultado = client.verify(transaccion_id, value, paymentez_uid(usuario), tipo)

        tx = resultado.transaction
        transaccion.estado = _estado_desde_resultado(resultado)
        transaccion.estado_paymentez = tx.get("current_status") or tx.get("status")
        transaccion.status_detail = tx.get("status_detail")
        transaccion.respuesta_cruda = resultado.data
        transaccion.save(update_fields=[
            "estado", "estado_paymentez", "status_detail",
            "respuesta_cruda", "fecha_actualizacion",
        ])

        if resultado.ok and not resultado.requiere_accion:
            _finalizar(transaccion)

        return resultado, transaccion
