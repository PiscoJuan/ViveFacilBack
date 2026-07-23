from rest_framework import serializers

from .models import TransaccionPaymentez


class TransaccionPaymentezAdminSerializer(serializers.ModelSerializer):
    """Datos de la transacción Paymentez para la vista admin de una solicitud."""

    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = TransaccionPaymentez
        fields = [
            "id", "estado", "estado_display", "estado_paymentez", "status_detail",
            "monto", "tipo_tarjeta", "bin", "codigo_autorizacion", "referencia",
            "fecha_creacion",
        ]


class DatosTarjetaSerializer(serializers.Serializer):
    """El token viene del SDK JS de Paymentez; el cvc lo confirma el usuario al
    pagar y solo se reenvía a Paymentez (nunca se guarda)."""

    token = serializers.CharField()
    cvc = serializers.CharField()


class PagarSerializer(serializers.Serializer):
    solicitud_id = serializers.IntegerField()
    datos_tarjeta = DatosTarjetaSerializer()
    cupon_codigo = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    datos_facturacion = serializers.DictField(required=False)
    browser_info = serializers.DictField(required=False)


class VerificarSerializer(serializers.Serializer):
    transaccion_id = serializers.CharField()
    value = serializers.CharField()
    tipo = serializers.ChoiceField(choices=["BY_OTP", "BY_CRES"], default="BY_OTP")


class EliminarTarjetaSerializer(serializers.Serializer):
    token = serializers.CharField()
