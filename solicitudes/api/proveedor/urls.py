from django.urls import path

from solicitudes.api.proveedor.views import (
    AddSolicitudProveedorView,
    EnvioProveedorView,
    HistorialSolicitudesProveedorView,
    InteresadosEnProcesoPagProveedorView,
    InteresadosPagEfectivoProveedorView,
    InteresadosPagProveedorView,
    InteresadosPagTarjetaProveedorView,
    InteresadosPasadasPagProveedorView,
    InteresadosPorFechaProveedorView,
    InteresadosProveedorView,
    SolicitudAdjudicadaProveedorView,
    SolicitudesPagadasProveedorView,
    SolicitudDetalleProveedorView,
    SolicitudPorServicioProveedorView,
    SolicitudProveedorView,
)

urlpatterns = [
    path("por-servicio/<str:ID_servicio>/", SolicitudPorServicioProveedorView.as_view()),
    path("envio/<str:solicitud_ID>", EnvioProveedorView.as_view()),
    # El id de proveedor va por URL, no se infiere de `request.user` — no
    # hay ownership-check server-side acá.
    path("interesados/lista/<str:id_proveedor_user_datos>/", InteresadosProveedorView.as_view()),
    path("interesados/<str:id_proveedor_user_datos>/", InteresadosPagProveedorView.as_view()),
    path("interesados/en-proceso/<str:id_proveedor_user_datos>/", InteresadosEnProcesoPagProveedorView.as_view()),
    path("interesados/pasadas/<str:id_proveedor_user_datos>/", InteresadosPasadasPagProveedorView.as_view()),
    path("interesados/fecha/<str:id_proveedor_user_datos>", InteresadosPorFechaProveedorView.as_view()),
    path("interesados/efectivo/<str:id_proveedor_user_datos>", InteresadosPagEfectivoProveedorView.as_view()),
    path("interesados/tarjeta/<str:id_proveedor_user_datos>", InteresadosPagTarjetaProveedorView.as_view()),
    path("pagadas/<str:id>", SolicitudesPagadasProveedorView.as_view()),
    path("crear/", AddSolicitudProveedorView.as_view()),
    path("<str:solicitud_ID>/detalle/", SolicitudDetalleProveedorView.as_view()),
    path("historial/<str:user>", HistorialSolicitudesProveedorView.as_view()),
    path("adjudicada/<str:solicitud_ID>", SolicitudAdjudicadaProveedorView.as_view()),
    path("", SolicitudProveedorView.as_view()),
    path("<str:solicitud_ID>", SolicitudProveedorView.as_view()),
]
