from django.urls import path

from content.api.web.views import InsigniasWebView, PoliticasWebView, TerminosCondicionesWebView

urlpatterns = [
    path("politicas/", PoliticasWebView.as_view()),
    path("politicas/<str:identifier>/", PoliticasWebView.as_view()),
    path("politica/", TerminosCondicionesWebView.as_view()),
    path("insignias/", InsigniasWebView.as_view()),
]
