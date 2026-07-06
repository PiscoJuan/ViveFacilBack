from django.urls import path

from promotions.api.web.views import ConfirmarDescuentoWebView

urlpatterns = [
    path("confirmar-descuento/<str:mail>/", ConfirmarDescuentoWebView.as_view()),
]
