from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from rest_framework.response import Response

from accounts import services
from api.serializers import SolicitanteSerializer
from api.versionamiento import VERSION_ANDROID_SOLICITANTE, VERSION_IOS_SOLICITANTE
from core.permissions import IsPublic
from core.views import SolicitanteAPIView


class LoginSolicitanteView(SolicitanteAPIView):
    """Un login no puede exigir estar ya autenticado, así que sobreescribe
    el permiso heredado de SolicitanteAPIView (IsSolicitante) por IsPublic —
    declarando explícitamente que es público a propósito, no un descuido
    (ver core/checks.py, que acepta IsPublic bajo cualquier namespace)."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        username = request.data.get("username")
        password = request.data.get("password")
        data, http_status = services.authenticate_login(
            request, username, password, expected_role="Solicitante"
        )
        return Response(data, status=http_status)


class CambioContraseniaSolicitanteView(SolicitanteAPIView):
    """Exige token válido de Firebase, no requiere estar ya logueado como
    Solicitante en este backend — igual que Login, es un endpoint de
    recuperación de acceso. Público (IsPublic), compartido con proveedor."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data, http_status = services.cambiar_contrasenia_firebase(
            request.data.get("token"), request.data.get("pass")
        )
        return Response(data, status=http_status)


class DispositivoNotificacionSolicitanteView(SolicitanteAPIView):
    def post(self, request, format=None):
        data, http_status = services.registrar_dispositivo(request, request.data.get("token"))
        return Response(data, status=http_status)

    def delete(self, request, format=None):
        correo = request.data.get("correo")
        data, http_status = services.eliminar_dispositivos_por_correo(correo)
        return Response(data, status=http_status)


class DatoSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (ver `DatoProveedorView`)."""

    def put(self, request, user, format=None):
        services.actualizar_datos_usuario(user, request.data, request.FILES)
        return Response(status=200)


class RegistroRedesSolicitanteView(SolicitanteAPIView):
    """Público (IsPublic): es parte del flujo de registro vía red social,
    no puede exigir sesión previa."""

    permission_classes = [IsPublic]

    def post(self, request, user, format=None):
        data, http_status = services.registrar_desde_redes(user, request.data, request.FILES)
        return Response(data, status=http_status)


class FacebookLoginSolicitanteView(SocialLoginView):
    """Exclusivo de Solicitante2022 (login.page.ts). Público (IsPublic): es
    login, no puede exigir sesión previa."""

    adapter_class = FacebookOAuth2Adapter
    permission_classes = [IsPublic]


class GoogleLoginSolicitanteView(SocialLoginView):
    """Ídem FacebookLoginSolicitanteView."""

    adapter_class = GoogleOAuth2Adapter
    permission_classes = [IsPublic]


class SolicitanteUserSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Admin (ver `SolicitanteUserAdminView`) —
    usado en login/registro/perfil propio."""

    def get(self, request, user, format=None):
        serializer = SolicitanteSerializer(services.obtener_solicitante_por_email(user), many=True)
        return Response(serializer.data)


class DatosUsuarioSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (ver `DatosUsuarioProveedorView`) —
    feature de chat, mostrar datos básicos de la contraparte."""

    def get(self, request, id, format=None):
        from api.serializers import DatosSerializer

        serializer = DatosSerializer(services.obtener_datos_por_user_id(id), many=True)
        return Response(serializer.data)


class CompleteDataUserSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (ver `CompleteDataUserProveedorView`)."""

    def put(self, request, username, format=None):
        return Response(services.completar_datos_usuario(username, request.data))


class RecuperarPasswordSolicitanteView(SolicitanteAPIView):
    """Exclusivo de Solicitante2022 (recuperar-contrasenia.page.ts) —
    Provedor2022 tiene un wrapper equivalente pero su recuperación real usa
    Firebase directo. Público (IsPublic): pre-login."""

    permission_classes = [IsPublic]

    def get(self, request, user_email, format=None):
        return Response({"success": services.recuperar_password_existe(user_email)})


class ValidarCodigoSolicitanteView(SolicitanteAPIView):
    """Mismo alcance real que RecuperarPasswordSolicitanteView."""

    permission_classes = [IsPublic]

    def get(self, request, email, codigo, format=None):
        return Response({"success": services.validar_codigo_recuperacion(email, codigo)})


class CambioPasswordCodigoSolicitanteView(SolicitanteAPIView):
    """Público (IsPublic): pre-login."""

    permission_classes = [IsPublic]

    def get(self, request, email, password, codigo, format=None):
        return Response({"success": services.cambiar_password_con_codigo(email, password, codigo)})


class PuntosSolicitanteView(SolicitanteAPIView):
    def get(self, request, email, format=None):
        return Response(services.obtener_puntos(email))


class VersionAndroidSolicitanteView(SolicitanteAPIView):
    """Público (IsPublic), mismo criterio que su análogo de proveedor
    (VersionAndroidProveedorView)."""

    permission_classes = [IsPublic]

    def get(self, request):
        return Response(VERSION_ANDROID_SOLICITANTE)


class VersionIosSolicitanteView(SolicitanteAPIView):
    """Ídem VersionAndroidSolicitanteView."""

    permission_classes = [IsPublic]

    def get(self, request):
        return Response(VERSION_IOS_SOLICITANTE)


class RegistroSolicitanteView(SolicitanteAPIView):
    """Alta real de Solicitante — misma lógica que
    `accounts.api.web.views.RegistroWebView` (un `ModelViewSet` por router,
    no una vista simple), llamada acá directo sin pasar por el router."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        return Response(services.crear_cuenta_registro(request.POST, request.FILES))
