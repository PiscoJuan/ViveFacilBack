from django.urls import path
from rest_framework.routers import DefaultRouter

from accounts.api.web.views import (
    ProveedorPendienteWebView,
    ProveedoresPendientesEmailWebView,
    ProveedorPublicoWebView,
    RegistroWebView,
)

router = DefaultRouter()
router.include_root_view = False  # sin esto, el root view autogenerado de DRF
# tropieza con core/checks.py (no hereda IsPublic) — no hace falta acá, un
# solo viewset registrado.
router.register(r"registro", RegistroWebView, basename="registro-web")

urlpatterns = router.urls + [
    path("proveedores-pendientes/", ProveedorPendienteWebView.as_view()),
    path("proveedores-pendientes/<str:mail>/", ProveedoresPendientesEmailWebView.as_view()),
    path("proveedor/<str:pk>/", ProveedorPublicoWebView.as_view()),
]
