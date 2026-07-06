from django.urls import path

from catalog.api.solicitante.views import ProveedoresPorServicioSolicitanteView

urlpatterns = [
    path("proveedores-por-servicio/<str:servicio_id>", ProveedoresPorServicioSolicitanteView.as_view()),
]
