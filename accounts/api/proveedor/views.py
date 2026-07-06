from rest_framework.response import Response

from accounts import services
from api.versionamiento import VERSION_ANDROID_PROVEEDOR, VERSION_IOS_PROVEEDOR
from core.permissions import IsPublic
from core.views import ProveedorAPIView


class LoginProveedorView(ProveedorAPIView):
    """Vista delgada de AuthService para el rol Proveedor — mismo mecanismo
    que LoginSolicitanteView (Fase 3). Reemplaza el branching manual que
    hoy vive en `Login.post()` (api/views.py:3504)."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        username = request.data.get("username")
        password = request.data.get("password")
        data, http_status = services.authenticate_login(
            request, username, password, expected_role="Proveedor"
        )
        return Response(data, status=http_status)


class CambioContraseniaProveedorView(ProveedorAPIView):
    """Réplica del endpoint multi-rol CambioContrasenia (api/views.py:713),
    ya extraído a `accounts.services` en la Fase 3."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data, http_status = services.cambiar_contrasenia_firebase(
            request.data.get("token"), request.data.get("pass")
        )
        return Response(data, status=http_status)


class DispositivoNotificacionProveedorView(ProveedorAPIView):
    """Réplica del endpoint multi-rol DeviceNotification (api/views.py:424),
    DELETE (cleanup checklist #23) y POST (cleanup checklist #22, antes
    servido bajo el path separado `post-token/` con la misma clase legacy
    — mismo `accounts.services.registrar_dispositivo` que ya usaba el
    POST legacy, solo se expone acá bajo namespace)."""

    def post(self, request, format=None):
        data, http_status = services.registrar_dispositivo(request, request.data.get("token"))
        return Response(data, status=http_status)

    def delete(self, request, format=None):
        correo = request.data.get("correo")
        data, http_status = services.eliminar_dispositivos_por_correo(correo)
        return Response(data, status=http_status)


class RegistroProveedorView(ProveedorAPIView):
    """Réplica de Register_Proveedor (api/views.py:1106). Sin evidencia de
    llamador real en ningún frontend — se migra igual por consistencia de
    namespace (ver accounts.services.registrar_proveedor)."""

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
    """Réplica de Documentos_proveedor (api/views.py:2285). Sin evidencia de
    llamador real en ningún frontend."""

    def put(self, request, username, format=None):
        data, http_status = services.actualizar_documento_proveedor(
            username, request.data.get("descripcion"), request.data
        )
        return Response(data, status=http_status)


class DatoProveedorView(ProveedorAPIView):
    """Réplica del PUT de Dato (api/views.py:2668), endpoint multi-rol
    compartido con Solicitante (ver DatoSolicitanteView en
    accounts/api/solicitante/views.py). El GET de esa misma clase no se
    tocó — sin evidencia de llamador real en ningún frontend."""

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
    """Réplica de SolicitanteByUserDatos.get (api/views.py:1648-1654).
    Confirmado real, exclusivo de Provedor2022 (feature de chat)."""

    def get(self, request, UserDatosId, format=None):
        from api.serializers import SolicitanteSerializer

        serializer = SolicitanteSerializer(
            services.obtener_solicitante_por_user_datos_id(UserDatosId), many=True)
        return Response(serializer.data)


class ChangePasswordProveedorView(ProveedorAPIView):
    """Réplica de ChangePassword (api/views.py:1976-2005), flujo de
    reactivación de cuenta de Proveedor vía `security_access`. Sin
    evidencia de llamador real en ningún frontend. Público (IsPublic):
    llega por un link de email, no hay sesión previa.

    El GET original (`super.get(request, *args, **kwargs)`) tiene un bug
    real y evidente — `super` sin invocar (`super.get`, no `super().get(...)`)
    lanza `AttributeError` en cualquier llamada exitosa. Se preserva tal
    cual (no se corrige): no hay evidencia de qué debía devolver el GET más
    allá de "confirmar que el token existe", y no hay llamador real que
    dependa de una respuesta concreta — inventar una sería adivinar
    comportamiento nuevo, no migrar el existente."""

    permission_classes = [IsPublic]

    def get(self, request, access_security, format=None):
        from api.models import Datos as _Datos

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
    """Réplica de Datos_Users.get (api/views.py:2221-2227), endpoint
    multi-rol compartido con Solicitante (ver DatosUsuarioSolicitanteView) —
    feature de chat."""

    def get(self, request, id, format=None):
        from api.serializers import DatosSerializer

        serializer = DatosSerializer(services.obtener_datos_por_user_id(id), many=True)
        return Response(serializer.data)


class CompleteDataUserProveedorView(ProveedorAPIView):
    """Réplica de Complete_Data_User.put (api/views.py:2230-2252), endpoint
    multi-rol sin evidencia de llamador real (ver también
    CompleteDataUserSolicitanteView)."""

    def put(self, request, username, format=None):
        return Response(services.completar_datos_usuario(username, request.data))


class ProveedorPorCorreoProveedorView(ProveedorAPIView):
    """Réplica de Get_ProveedorByUser.get (api/views.py:1339-1345).
    Confirmado real: se usa durante el login (`getProveedorByCorreo`,
    login.page.ts) — antes de tener token, por eso queda público."""

    permission_classes = [IsPublic]

    def get(self, request, user, format=None):
        return Response(services.obtener_proveedor_por_correo(user))


class ProveedorRegistroManualView(ProveedorAPIView):
    """Réplica de ProveedorRegistro (api/views.py:2662-2746). Sin evidencia
    de llamador real en ningún frontend — segundo mecanismo de alta de
    proveedor distinto de RegistroProveedorView. Público (IsPublic): alta
    de cuenta nueva, sin sesión previa."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data = services.registrar_proveedor_manual(request.data, request.FILES)
        return Response(data)
