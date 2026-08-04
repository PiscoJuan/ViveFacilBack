"""Página pública de cambio de contraseña (el destino del enlace que sale en el
correo de recuperación).

Va como vista de Django y no como APIView de DRF a propósito: lo que se sirve
acá es HTML para el navegador, no JSON para las apps.
"""
import logging

from django.shortcuts import render
from django.views import View

from accounts import services

logger = logging.getLogger(__name__)

TEMPLATE = "password/cambiar_contrasena.html"


class CambiarContrasenaView(View):
    def get(self, request, uidb64, token):
        usuario = services.usuario_por_token_recuperacion(uidb64, token)
        if usuario is None:
            return render(request, TEMPLATE, {"estado": "invalido"})
        return render(request, TEMPLATE, {
            "estado": "form",
            "username": services.nombre_para_saludo(usuario),
        })

    def post(self, request, uidb64, token):
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        usuario = services.usuario_por_token_recuperacion(uidb64, token)
        if usuario is None:
            return render(request, TEMPLATE, {"estado": "invalido"})

        password1 = request.POST.get("password1") or ""
        password2 = request.POST.get("password2") or ""

        errores = []
        if password1 != password2:
            errores.append("Las dos contraseñas no coinciden.")
        else:
            try:
                validate_password(password1, usuario)
            except ValidationError as e:
                errores.extend(e.messages)

        if not errores:
            # Reusa el cambio del panel de admin: actualiza Django y Firebase
            # (que es donde de verdad vive la contraseña con la que entran las
            # apps) y borra el token DRF de las sesiones abiertas.
            ok, mensaje = services.cambiar_password_usuario(usuario.id, password1)
            if not ok:
                logger.error("Cambio de contraseña por enlace falló: %s", mensaje)
                errores.append("No pudimos guardar la contraseña. Inténtalo de nuevo en unos minutos.")

        if errores:
            return render(request, TEMPLATE, {
                "estado": "form",
                "username": services.nombre_para_saludo(usuario),
                "errores": errores,
            })

        return render(request, TEMPLATE, {"estado": "ok"})
