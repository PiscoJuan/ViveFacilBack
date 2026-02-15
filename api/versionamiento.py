from enum import Enum
import json
from django.http import JsonResponse

class AppMovil(str, Enum):
    SOLICITANTE = "solicitante"
    PROVEEDOR = "proveedor"

class Plataforma(str, Enum):
    ANDROID = "android"
    IOS = "ios"

VERSION_ANDROID_SOLICITANTE = "1"
VERSION_IOS_SOLICITANTE = "1"
VERSION_ANDROID_PROVEEDOR = "1"
VERSION_IOS_PROVEEDOR = "1"

VERSIONES = {
    AppMovil.SOLICITANTE: {
        Plataforma.ANDROID: VERSION_ANDROID_SOLICITANTE,
        Plataforma.IOS: VERSION_IOS_SOLICITANTE,
    },
    AppMovil.PROVEEDOR: {
        Plataforma.ANDROID: VERSION_ANDROID_PROVEEDOR,
        Plataforma.IOS: VERSION_IOS_PROVEEDOR,
    },
}
def validar_header_versionamiento(payload):
    required_fields = {"app", "plataforma", "version"}

    # Debe ser un dict
    if not isinstance(payload, dict):
        return False, "El header debe ser un objeto JSON"

    # Campos faltantes
    missing = required_fields - payload.keys()
    if missing:
        return False, f"Faltan campos: {', '.join(missing)}"

    # Tipos esperados
    if not isinstance(payload["app"], str):
        return False, "El campo 'app' debe ser string"

    if not isinstance(payload["plataforma"], str):
        return False, "El campo 'plataforma' debe ser string"

    if not isinstance(payload["version"], (str, int)):
        return False, "El campo 'version' debe ser string o número"

    return True, None

class VersionamientoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        header_value = request.headers.get("versionamiento")
        # Si no envía header → permitir (útil para web u otros clientes)
        if not header_value:
            return self.get_response(request)
        # Validar JSON
        try:
            payload = json.loads(header_value)
        except Exception:
            return JsonResponse({"message": "El formato de versionamiento es inválido"}, status=400)

        valido, error = validar_header_versionamiento(payload)
        if not valido:
            return JsonResponse({"message": error}, status=400)

        app_raw = str(payload.get("app", "")).strip().lower()
        plataforma_raw = str(payload.get("plataforma", "")).strip().lower()
        version = str(payload.get("version", "")).strip()

        # VALIDAR ENUMS
        try:
            app = AppMovil(app_raw)
        except ValueError:
            return JsonResponse(
                {"message": f"La app '{app_raw}' no es válida"},
                status=400,
            )

        try:
            plataforma = Plataforma(plataforma_raw)
        except ValueError:
            return JsonResponse(
                {"message": f"La plataforma '{plataforma_raw}' no es válida"},
                status=400,
            )

        # VALIDAR VERSION
        expected_version = VERSIONES.get(app, {}).get(plataforma)
        if expected_version is None:
            return JsonResponse(
                {"message": "Configuración de versión no encontrada"},
                status=500,
            )

        if version != expected_version:
            return JsonResponse(
                {"message": "Debe actualizar a una versión más reciente"},
                status=426,
            )

        return self.get_response(request)
