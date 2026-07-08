from django.contrib import admin

from pagos.models import ConfiguracionPaymentez, TransaccionPaymentez


@admin.register(ConfiguracionPaymentez)
class ConfiguracionPaymentezAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ambiente", "is_active", "eliminar_tarjeta_tras_compra", "fecha_actualizacion")
    list_filter = ("ambiente", "is_active")
    readonly_fields = ("fecha_creacion", "fecha_actualizacion")
    fieldsets = (
        (None, {"fields": ("nombre", "ambiente", "is_active", "eliminar_tarjeta_tras_compra")}),
        ("Credenciales", {"fields": ("app_code_client", "app_key_client", "app_code_server", "app_key_server", "url_base")}),
        ("Auditoría", {"fields": ("fecha_creacion", "fecha_actualizacion")}),
    )


@admin.register(TransaccionPaymentez)
class TransaccionPaymentezAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "estado", "monto", "tipo_tarjeta", "bin", "solicitud", "fecha_creacion")
    list_filter = ("estado", "tipo_tarjeta")
    search_fields = ("id", "referencia", "codigo_autorizacion", "usuario__username", "usuario__email")
    raw_id_fields = ("usuario", "solicitud", "pago_tarjeta")
    readonly_fields = [
        "id", "usuario", "solicitud", "pago_tarjeta", "referencia",
        "codigo_autorizacion", "referencia_dev", "tipo_tarjeta", "bin",
        "card_token", "monto", "estado", "estado_paymentez", "status_detail",
        "threeds_ctx", "threeds_data", "respuesta_cruda", "datos_facturacion",
        "fecha_creacion", "fecha_actualizacion",
    ]

    def has_add_permission(self, request):
        return False
