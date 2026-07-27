from django.urls import path

from payments.api.solicitante.views import EmailFacturaSolicitanteView, PagoEfectivoSolicitanteView

urlpatterns = [
    path("pago-efectivo/", PagoEfectivoSolicitanteView.as_view()),
    path("factura/", EmailFacturaSolicitanteView.as_view()),
]
