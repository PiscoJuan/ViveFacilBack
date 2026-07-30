from django.urls import path

from promotions.api.web.views import (
    ConfirmarDescuentoWebView,
    CuponCantidadWebView,
    CuponDetalleWebView,
    CuponesCategoriaWebView,
)

urlpatterns = [
    path("confirmar-descuento/<str:mail>/", ConfirmarDescuentoWebView.as_view()),
    path("cupones/<str:pk>/", CuponDetalleWebView.as_view()),
    path("cupones/<str:pk>/cantidad/", CuponCantidadWebView.as_view()),
    path("cupones/categoria/<str:cupCode>/", CuponesCategoriaWebView.as_view()),
]
