from rest_framework.response import Response

from accounts import services
from api.versionamiento import VERSION_ANDROID_PROVEEDOR, VERSION_IOS_PROVEEDOR
from core.permissions import IsPublic
from core.views import ProveedorAPIView


class LoginProveedorView(ProveedorAPIView):
    permission_classes = [IsPublic]

    def post(self, request, format=None):
        username = request.data.get("username")
        password = request.data.get("password")
        data, http_status = services.authenticate_login(
            request, username, password, expected_role="Proveedor"
        )
        return Response(data, status=http_status)


class CambioContraseniaProveedorView(ProveedorAPIView):
    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data, http_status = services.cambiar_contrasenia_firebase(
            request.data.get("token"), request.data.get("pass")
        )
        return Response(data, status=http_status)


class DispositivoNotificacionProveedorView(ProveedorAPIView):
    def post(self, request, format=None):
        data, http_status = services.registrar_dispositivo(request, request.data.get("token"))
        return Response(data, status=http_status)

    def delete(self, request, format=None):
        correo = request.data.get("correo")
        data, http_status = services.eliminar_dispositivos_por_correo(correo)
        return Response(data, status=http_status)


class RegistroProveedorView(ProveedorAPIView):
    permission_classes = [IsPublic]  # alta de cuenta nueva, no hay sesión de Proveedor todavía

    def post(self, request, format=None):
        data, http_status = services.registrar_proveedor(
            email=request.POST.get("email"),
            tipo=request.POST.get("tipo"),
            nombres=request.POST.get("nombres"),
            apellidos=request.POST.get("apellidos"),
            telefono=request.POST.get("telefono"),
            genero=request.POST.get("genero"),
            foto=request.FILES.get("foto"),
        )
        return Response(data, status=http_status)


class DocumentoProveedorView(ProveedorAPIView):
    def put(self, request, username, format=None):
        data, http_status = services.actualizar_documento_proveedor(
            username, request.data.get("descripcion"), request.data
        )
        return Response(data, status=http_status)


class DatoProveedorView(ProveedorAPIView):
    """Endpoint compartido con Solicitante (ver `DatoSolicitanteView`)."""

    def put(self, request, user, format=None):
        services.actualizar_datos_usuario(user, request.data, request.FILES)
        return Response(status=200)


class VersionAndroidProveedorView(ProveedorAPIView):
    permission_classes = [IsPublic]  # consulta de versión mínima, sin sesión

    def get(self, request):
        return Response(VERSION_ANDROID_PROVEEDOR)


class VersionIosProveedorView(ProveedorAPIView):
    permission_classes = [IsPublic]

    def get(self, request):
        return Response(VERSION_IOS_PROVEEDOR)


class SolicitanteByUserDatosProveedorView(ProveedorAPIView):
    def get(self, request, UserDatosId, format=None):
        from api.serializers import SolicitanteSerializer

        serializer = SolicitanteSerializer(
            services.obtener_solicitante_por_user_datos_id(UserDatosId), many=True)
        return Response(serializer.data)


class ChangePasswordProveedorView(ProveedorAPIView):
    """Flujo de reactivación de cuenta de Proveedor vía `security_access`.
    Público (IsPublic): llega por un link de email, no hay sesión previa.

    El GET original (`super.get(request, *args, **kwargs)`) tiene un bug
    real y evidente — `super` sin invocar (`super.get`, no `super().get(...)`)
    lanza `AttributeError` en cualquier llamada exitosa. Se preserva tal
    cual (no se corrige): no hay evidencia de qué debía devolver el GET más
    allá de "confirmar que el token existe", y no hay llamador real que
    dependa de una respuesta concreta — inventar una sería adivinar
    comportamiento nuevo, no migrar el existente."""

    permission_classes = [IsPublic]

    def get(self, request, access_security, format=None):
        from accounts.models import Datos as _Datos

        if _Datos.objects.filter(security_access=access_security).exists():
            return super().get(request, access_security, format)
        from rest_framework import status as _status
        return Response(status=_status.HTTP_400_BAD_REQUEST)

    def post(self, request, access_security, format=None):
        from rest_framework import status as _status

        try:
            data = services.reactivar_cuenta_proveedor(access_security, request.data.get('password'))
            return Response(data)
        except Exception as e:
            return Response({"error": str(e)}, status=_status.HTTP_400_BAD_REQUEST)


class DatosUsuarioProveedorView(ProveedorAPIView):
    """Endpoint compartido con Solicitante (ver `DatosUsuarioSolicitanteView`) — feature de chat."""

    def get(self, request, id, format=None):
        from api.serializers import DatosSerializer

        serializer = DatosSerializer(services.obtener_datos_por_user_id(id), many=True)
        return Response(serializer.data)


class CompleteDataUserProveedorView(ProveedorAPIView):
    """Endpoint compartido con Solicitante (ver `CompleteDataUserSolicitanteView`)."""

    def put(self, request, username, format=None):
        return Response(services.completar_datos_usuario(username, request.data))


class ProveedorPorCorreoProveedorView(ProveedorAPIView):
    """Se usa durante el login (`getProveedorByCorreo`, login.page.ts) —
    antes de tener token, por eso queda público."""

    permission_classes = [IsPublic]

    def get(self, request, user, format=None):
        return Response(services.obtener_proveedor_por_correo(user))


class ProveedorRegistroManualView(ProveedorAPIView):
    """Segundo mecanismo de alta de proveedor, distinto de
    `RegistroProveedorView`. Público (IsPublic): alta de cuenta nueva, sin
    sesión previa."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data = services.registrar_proveedor_manual(request.data, request.FILES)
        return Response(data)
