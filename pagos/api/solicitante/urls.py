from django.urls import path

from pagos.api.solicitante.views import (
    ConfigClienteView,
    EliminarTarjetaView,
    ListarTarjetasView,
    PagarView,
    Paymentez3DSTermView,
    VerificarEstadoView,
    VerificarView,
    WebhookPaymentezView,
)

urlpatterns = [
    path("config-cliente/", ConfigClienteView.as_view()),
    path("pagar/", PagarView.as_view()),
    path("verificar/", VerificarView.as_view()),
    path("verificar-estado/<str:transaccion_id>/", VerificarEstadoView.as_view()),
    path("tarjetas/", ListarTarjetasView.as_view()),
    path("tarjetas/eliminar/", EliminarTarjetaView.as_view()),
    # Callbacks públicos de Paymentez (validados por stoken / ctx):
    path("webhook/", WebhookPaymentezView.as_view()),
    path("3ds-term/<str:ctx>/", Paymentez3DSTermView.as_view()),
]
