from django.urls import path

from catalog.api.proveedor.views import MisProfesionesProveedorView

urlpatterns = [
    path("mis-profesiones/", MisProfesionesProveedorView.as_view()),
]
