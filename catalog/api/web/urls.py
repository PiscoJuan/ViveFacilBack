from django.urls import path

from catalog.api.web.views import ProfesionesWebView, ServiciosWebView

urlpatterns = [
    path("profesiones/", ProfesionesWebView.as_view()),
    path("servicios/", ServiciosWebView.as_view()),
]
