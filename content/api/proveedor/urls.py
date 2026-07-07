from django.urls import path

from content.api.proveedor.views import (
    InsigniasPersonalesProveedorView,
    InsigniasProveedorView,
    MedallasPersonalesProveedorView,
    PoliticasProveedorView,
    SugerenciasProveedorView,
)

urlpatterns = [
    path("insignias/", InsigniasProveedorView.as_view()),
    path("politicas/", PoliticasProveedorView.as_view()),
    path("insignias-personales/<str:id>", InsigniasPersonalesProveedorView.as_view()),
    path("medallas-personales/", MedallasPersonalesProveedorView.as_view()),
    path("sugerencias/", SugerenciasProveedorView.as_view()),
]
