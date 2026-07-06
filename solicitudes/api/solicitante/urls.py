from django.urls import path

from solicitudes.api.solicitante.views import (
    AddSolicitudSolicitanteView,
    AdjudicarSolicitudSolicitanteView,
    EnvioInteresadosSolicitanteView,
    HistorialSolicitudesSolicitanteView,
    SolicitudAdjudicadaSolicitanteView,
    SolicitudDetalleSolicitanteView,
    SolicitudesEnProcesoSolicitanteView,
    SolicitudesNoPagadasPagSolicitanteView,
    SolicitudesNoPagadasSolicitanteView,
    SolicitudesPagadasPagSolicitanteView,
    SolicitudesPagadasSolicitanteView,
    SolicitudesPasadasPagSolicitanteView,
    SolicitudesPasadasSolicitanteView,
    SolicitudesPendientesPagSolicitanteView,
    SolicitudesPendientesSolicitanteView,
    SolicitudSolicitanteView,
)

# IMPORTANTE: los paths literales de un solo segmento (crear/, en-proceso/,
# pasadas-pag/) tienen que ir ANTES que `<str:solicitud_ID>`, si no ese
# catch-all de un segmento los intercepta primero y devuelve 405 (bug real
# encontrado en la verificación en vivo de esta fase — Django resuelve
# urlpatterns en orden).
#
# Los parámetros de path NO llevan `/` final a propósito: el frontend
# (ViveFacil_Solicitante2022) arma estas URLs con concatenación de string
# (`baseUrl + id`), sin slash final — igual que el estilo del `api/urls.py`
# legacy.
urlpatterns = [
    path("pendientes/<str:correo>", SolicitudesPendientesSolicitanteView.as_view()),
    path("pendientes-pag/<str:correo>", SolicitudesPendientesPagSolicitanteView.as_view()),
    path("pasadas/<str:correo>", SolicitudesPasadasSolicitanteView.as_view()),
    path("pasadas-pag/", SolicitudesPasadasPagSolicitanteView.as_view()),
    path("pagadas/<str:correo>", SolicitudesPagadasSolicitanteView.as_view()),
    path("pagadas-pag/<str:correo>", SolicitudesPagadasPagSolicitanteView.as_view()),
    path("no-pagadas/<str:correo>", SolicitudesNoPagadasSolicitanteView.as_view()),
    path("no-pagadas-pag/<str:correo>", SolicitudesNoPagadasPagSolicitanteView.as_view()),
    path("en-proceso/", SolicitudesEnProcesoSolicitanteView.as_view()),
    path("interesados/<str:solicitud_ID>", EnvioInteresadosSolicitanteView.as_view()),
    path("adjudicar/<str:solicitud_ID>", AdjudicarSolicitudSolicitanteView.as_view()),
    path("crear/", AddSolicitudSolicitanteView.as_view()),
    path("<str:solicitud_ID>/detalle/", SolicitudDetalleSolicitanteView.as_view()),
    path("historial/<str:user>", HistorialSolicitudesSolicitanteView.as_view()),
    path("adjudicada/<str:solicitud_ID>", SolicitudAdjudicadaSolicitanteView.as_view()),
    path("", SolicitudSolicitanteView.as_view()),
    path("<str:solicitud_ID>", SolicitudSolicitanteView.as_view()),
]
