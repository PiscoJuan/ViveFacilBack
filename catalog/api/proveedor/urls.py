from django.urls import path

from catalog.api.proveedor.views import CiudadesProveedorView, MisProfesionesProveedorView, SolicitudProfesionProveedorView

urlpatterns = [
    path("mis-profesiones/", MisProfesionesProveedorView.as_view()),
    path("solicitudes-profesion/crear/", SolicitudProfesionProveedorView.as_view()),
    path("ciudades/", CiudadesProveedorView.as_view()),
]
