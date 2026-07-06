from django.urls import path

from content.api.admin.views import (
    CargoDetailsAdminView,
    CargosAdminView,
    InsigniaDetailsAdminView,
    InsigniasAdminView,
    MedallaEstadoAdminView,
    MedallasAdminView,
    PublicidadesAdminView,
    PublicidadesBuscarAdminView,
    ReadSuggestionsAdminView,
    SuggestionsDetalleAdminView,
    UnreadSuggestionsAdminView,
)

urlpatterns = [
    path("insignias/<str:id>/", InsigniasAdminView.as_view()),
    path("insignias/detalle/<str:pk>/", InsigniaDetailsAdminView.as_view()),
    path("insignias/estado/", InsigniaDetailsAdminView.as_view()),
    path("medallas/", MedallasAdminView.as_view()),
    path("medallas/<str:id>/", MedallasAdminView.as_view()),
    path("medallas/estado/", MedallaEstadoAdminView.as_view()),
    path("cargos/", CargosAdminView.as_view()),
    path("cargos/<str:id>/", CargosAdminView.as_view()),
    path("cargos/detalle/<str:pk>/", CargoDetailsAdminView.as_view()),
    path("publicidades/", PublicidadesAdminView.as_view()),
    path("publicidades/<str:id>/", PublicidadesAdminView.as_view()),
    path("publicidades/buscar/", PublicidadesBuscarAdminView.as_view()),
    path("suggestions/read/", ReadSuggestionsAdminView.as_view()),
    path("suggestions/unread/", UnreadSuggestionsAdminView.as_view()),
    path("suggestions/<str:pk>/", SuggestionsDetalleAdminView.as_view()),
    path("suggestions/estado/", SuggestionsDetalleAdminView.as_view()),
]
