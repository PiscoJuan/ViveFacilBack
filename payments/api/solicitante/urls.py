from django.urls import path

from payments.api.solicitante.views import (
    EmailFacturaSolicitanteView,
    PagoEfectivoSolicitanteView,
    PagoTarjetaSolicitanteView,
    TarjetaSolicitanteView,
    TarjetaUserSolicitanteView,
)

urlpatterns = [
    path("pago-efectivo/", PagoEfectivoSolicitanteView.as_view()),
    path("pago-tarjeta/", PagoTarjetaSolicitanteView.as_view()),
    path("factura/", EmailFacturaSolicitanteView.as_view()),
    path("tarjeta/", TarjetaSolicitanteView.as_view()),
    path("tarjeta/<str:identifier>", TarjetaUserSolicitanteView.as_view()),
]
