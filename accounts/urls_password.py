"""Rutas HTML públicas de cuenta (no van bajo administrador/proveedor/
solicitante/web: no son API de ninguna app, es una página que abre el
navegador desde el correo)."""
from django.urls import path

from accounts.views_password import CambiarContrasenaView

urlpatterns = [
    path("cambiar-contrasena/<str:uidb64>/<str:token>/", CambiarContrasenaView.as_view()),
]
