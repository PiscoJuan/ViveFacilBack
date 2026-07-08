from django.conf import settings
from django.db import models


class AmbientePaymentez(models.TextChoices):
    STAGING = "stg", "Staging"
    PRODUCCION = "prod", "Producción"


class ConfiguracionPaymentez(models.Model):
    """
    Credenciales y configuración de Paymentez. Se administra desde el admin de
    Django. La fila marcada con is_active=True es la que usa el sistema.
    Las llaves *_server nunca se exponen al cliente.
    """

    nombre = models.CharField(
        max_length=100,
        default="Configuración Paymentez",
        help_text="Nombre descriptivo de esta configuración.",
    )
    app_code_client = models.CharField(max_length=255)
    app_key_client = models.CharField(max_length=255)
    app_code_server = models.CharField(max_length=255)
    app_key_server = models.CharField(max_length=255)
    url_base = models.CharField(
        max_length=255,
        default="https://ccapi-stg.paymentez.com/v2/",
        help_text="Debe terminar en '/'. Ej: https://ccapi-stg.paymentez.com/v2/",
    )
    ambiente = models.CharField(
        max_length=10,
        choices=AmbientePaymentez.choices,
        default=AmbientePaymentez.STAGING,
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Solo una configuración debe estar activa a la vez.",
    )
    eliminar_tarjeta_tras_compra = models.BooleanField(
        default=False,
        help_text=(
            "Si está activo, la tarjeta usada se elimina de Paymentez al "
            "finalizar la compra (tarjetas de un solo uso). Desactívalo para "
            "permitir tarjetas guardadas (caso ViveFacil)."
        ),
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pagos_configuracion_paymentez"
        verbose_name = "Configuración Paymentez"
        verbose_name_plural = "Configuraciones Paymentez"

    def __str__(self):
        estado = "activa" if self.is_active else "inactiva"
        return f"{self.nombre} ({self.get_ambiente_display()}, {estado})"


class EstadoTransaccion(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    APROBADA = "aprobada", "Aprobada"
    RECHAZADA = "rechazada", "Rechazada"
    CANCELADA = "cancelada", "Cancelada"


class TransaccionPaymentez(models.Model):
    """
    Registro local de una transacción de Paymentez. El id es el id de la
    transacción que devuelve Paymentez (transaction/debit).

    A diferencia de la radio (Carrito -> Orden), aquí se paga una `Solicitud`
    ya existente. El `pago_tarjeta` se enlaza solo cuando el pago se aprueba.
    Nunca se guarda el CVC.
    """

    id = models.CharField(max_length=255, primary_key=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="transacciones_paymentez",
    )
    # db_constraint=False: las tablas legacy (api_solicitud, api_pagotarjeta)
    # usan PK int mientras estas apps declaran BigAutoField, así que MySQL
    # rechaza el FK por tipos incompatibles. Se omite la constraint a nivel de
    # BD (el ORM y los joins siguen igual). ponytail: si se normalizan los PK a
    # bigint en el futuro, quitar este flag y recrear las constraints.
    solicitud = models.ForeignKey(
        "solicitudes.Solicitud",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="transacciones_paymentez",
        help_text="Qué se está pagando.",
    )
    # El registro contable (PagoTarjeta) se crea solo al aprobarse el pago.
    pago_tarjeta = models.ForeignKey(
        "payments.PagoTarjeta",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_constraint=False,
        related_name="transacciones_paymentez",
        help_text="Se enlaza cuando el pago se aprueba.",
    )
    datos_facturacion = models.JSONField(null=True, blank=True)
    referencia = models.CharField(max_length=255, null=True, blank=True)
    codigo_autorizacion = models.CharField(max_length=255, null=True, blank=True)
    referencia_dev = models.CharField(max_length=255, null=True, blank=True)
    tipo_tarjeta = models.CharField(max_length=100, null=True, blank=True)
    bin = models.CharField(max_length=10, null=True, blank=True)
    # token de la tarjeta en Paymentez (no es el PAN).
    card_token = models.CharField(max_length=255, null=True, blank=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # estado interno simplificado
    estado = models.CharField(
        max_length=20,
        choices=EstadoTransaccion.choices,
        default=EstadoTransaccion.PENDIENTE,
    )
    # estado crudo y detalle que devuelve Paymentez (current_status / status_detail)
    estado_paymentez = models.CharField(max_length=50, null=True, blank=True)
    status_detail = models.IntegerField(null=True, blank=True)
    threeds_ctx = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    threeds_data = models.JSONField(null=True, blank=True)
    respuesta_cruda = models.JSONField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pagos_transaccion_paymentez"
        verbose_name = "Transacción Paymentez"
        verbose_name_plural = "Transacciones Paymentez"
        ordering = ["-fecha_creacion"]
        indexes = [
            models.Index(fields=["referencia"]),
            models.Index(fields=["threeds_ctx"]),
            models.Index(fields=["estado"]),
        ]

    def __str__(self):
        return f"{self.id} - {self.get_estado_display()} (${self.monto})"
