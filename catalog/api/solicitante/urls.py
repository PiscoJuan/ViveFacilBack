from django.urls import path

from catalog.api.solicitante.views import (
    CategoriasSolicitanteView,
    CiudadesSolicitanteView,
    ProveedoresPorServicioSolicitanteView,
    ServiciosSolicitanteView,
)

urlpatterns = [
    path("proveedores-por-servicio/<str:servicio_id>", ProveedoresPorServicioSolicitanteView.as_view()),
    path("categorias/", CategoriasSolicitanteView.as_view()),
    path("servicios/", ServiciosSolicitanteView.as_view()),
    path("ciudades/", CiudadesSolicitanteView.as_view()),
]
