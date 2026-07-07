from django.urls import path

from promotions.api.web.views import (
    AllPromocionesCategoriaWebView,
    ConfirmarDescuentoWebView,
    CuponCantidadWebView,
    CuponDetalleWebView,
    CuponesCategoriaWebView,
    PromocionesCategoriaWebView,
    PromocionesWebView,
)

urlpatterns = [
    path("confirmar-descuento/<str:mail>/", ConfirmarDescuentoWebView.as_view()),
    path("promociones/", PromocionesWebView.as_view()),
    path("promociones/categoria/<str:promCode>/", PromocionesCategoriaWebView.as_view()),
    path("promociones/categoria/", AllPromocionesCategoriaWebView.as_view()),
    path("cupones/<str:pk>/", CuponDetalleWebView.as_view()),
    path("cupones/<str:pk>/cantidad/", CuponCantidadWebView.as_view()),
    path("cupones/categoria/<str:cupCode>/", CuponesCategoriaWebView.as_view()),
]
