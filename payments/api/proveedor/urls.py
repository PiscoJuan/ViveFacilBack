from django.urls import path

from payments.api.proveedor.views import CuentaProveedorView, TarjetaUserProveedorView

urlpatterns = [
    path("cuenta/<str:proveedorID>/", CuentaProveedorView.as_view()),
    path("tarjeta/<str:identifier>", TarjetaUserProveedorView.as_view()),
]
