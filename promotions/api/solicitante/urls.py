from django.urls import path

from promotions.api.solicitante.views import (
    CuponAplicadoCrearSolicitanteView,
    CuponAplicadoPagSolicitanteView,
    CuponAplicadoSolicitanteView,
    CuponCategoriaPagSolicitanteView,
    CuponCategoriaSolicitanteView,
    RevisarDescuentoUnicoSolicitanteView,
    UsarDescuentoUnicoSolicitanteView,
)

urlpatterns = [
    path("cupon-aplicado/<str:user>", CuponAplicadoSolicitanteView.as_view()),
    path("cupon-aplicado/", CuponAplicadoCrearSolicitanteView.as_view()),
    path("cupon-aplicado-pag/<str:user>", CuponAplicadoPagSolicitanteView.as_view()),
    path("cupon-categorias/", CuponCategoriaSolicitanteView.as_view()),
    path("cupon-categorias-pag/", CuponCategoriaPagSolicitanteView.as_view()),
    path("revisar-descuento-unico/", RevisarDescuentoUnicoSolicitanteView.as_view()),
    path("usar-descuento-unico/<str:mail>", UsarDescuentoUnicoSolicitanteView.as_view()),
]
