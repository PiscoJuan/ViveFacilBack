from django.urls import path

from catalog.api.admin.views import (
    CategoriasAdminView,
    CiudadesAdminView,
    CrearProfesionesFaltantesAdminView,
    ManejoSolicitudAdminView,
    ProfesionesAdminView,
    ProfesionProveedorAdminView,
    ServiciosAdminView,
    SincronizarProfesionProveedorAdminView,
    SolicitudesProfesionAdminView,
    SolicitudesProfesionBusquedaAdminView,
    SolicitudesProfesionFechaAdminView,
    SolicitudPorUsuarioAdminView,
    SolicitudProfesionDetalleAdminView,
)

urlpatterns = [
    path("categorias/", CategoriasAdminView.as_view()),
    path("categorias/<str:id>/", CategoriasAdminView.as_view()),
    path("servicios/<str:id>/", ServiciosAdminView.as_view()),
    path("profesiones/<str:pk>/", ProfesionesAdminView.as_view()),
    path("ciudades/", CiudadesAdminView.as_view()),
    path("crear-profesiones-faltantes/", CrearProfesionesFaltantesAdminView.as_view()),
    path("profesion-proveedor/<str:proveedor_id>/", ProfesionProveedorAdminView.as_view()),
    path("sincronizar-profesion-proveedor/", SincronizarProfesionProveedorAdminView.as_view()),
    path("solicitudes-profesion/", SolicitudesProfesionAdminView.as_view()),
    path("solicitudes-profesion/usuario/<str:user>/", SolicitudPorUsuarioAdminView.as_view()),
    path("solicitudes-profesion/gestion/", ManejoSolicitudAdminView.as_view()),
    path("solicitudes-profesion/gestion/<str:pk>/", ManejoSolicitudAdminView.as_view()),
    path("solicitudes-profesion/buscar/<str:user>/", SolicitudesProfesionBusquedaAdminView.as_view()),
    path("solicitudes-profesion/fecha/", SolicitudesProfesionFechaAdminView.as_view()),
    path("solicitudes-profesion/<str:pk>/", SolicitudProfesionDetalleAdminView.as_view()),
]
