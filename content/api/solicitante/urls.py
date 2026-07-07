from django.urls import path

from content.api.solicitante.views import (
    InsigniasPersonalesSolicitanteView,
    InsigniasSolicitanteView,
    MedallasPersonalesSolicitanteView,
    PoliticasSolicitanteView,
    SugerenciasSolicitanteView,
)

urlpatterns = [
    path("politicas/", PoliticasSolicitanteView.as_view()),
    path("insignias-personales/<str:id>", InsigniasPersonalesSolicitanteView.as_view()),
    path("medallas-personales/", MedallasPersonalesSolicitanteView.as_view()),
    path("insignias-solicitante/", InsigniasSolicitanteView.as_view()),
    path("sugerencias/", SugerenciasSolicitanteView.as_view()),
]
