from django.urls import path

from notifications.api.web.views import NotificacionAnuncioWebView

urlpatterns = [
    path("notificacion-anuncio/", NotificacionAnuncioWebView.as_view()),
    path("notificacion-anuncio/<str:id>/", NotificacionAnuncioWebView.as_view()),
]
