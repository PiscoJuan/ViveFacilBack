from django.urls import path

from promotions.api.solicitante.views import (
    CuponAplicadoCrearSolicitanteView,
    CuponAplicadoSolicitanteView,
    CuponCategoriaSolicitanteView,
    PromocionesSolicitanteView,
    RevisarDescuentoUnicoSolicitanteView,
    UsarDescuentoUnicoSolicitanteView,
)

urlpatterns = [
    path("promociones/", PromocionesSolicitanteView.as_view()),
    path("cupon-aplicado/<str:user>", CuponAplicadoSolicitanteView.as_view()),
    path("cupon-aplicado/", CuponAplicadoCrearSolicitanteView.as_view()),
    path("cupon-categorias/", CuponCategoriaSolicitanteView.as_view()),
    path("revisar-descuento-unico/", RevisarDescuentoUnicoSolicitanteView.as_view()),
    path("usar-descuento-unico/<str:mail>", UsarDescuentoUnicoSolicitanteView.as_view()),
]
