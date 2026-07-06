from django.urls import path

from content.api.web.views import PoliticasWebView, TerminosCondicionesWebView

urlpatterns = [
    path("politicas/", PoliticasWebView.as_view()),
    path("politica/", TerminosCondicionesWebView.as_view()),
]
