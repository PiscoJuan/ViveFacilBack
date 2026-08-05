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
        data, http_status = services.registrar_dispositivo(
            request, request.data.get("token"), request.data.get("tipo") or request.data.get("type")
        )
        return Response(data, status=http_status)

    def delete(self, request, format=None):
        correo = request.data.get("correo")
        data, http_status = services.eliminar_dispositivos_por_correo(correo)
        return Response(data, status=http_status)


class DatoSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (ver `DatoProveedorView`).

    Sin `<user>` en la URL a propósito: el registro a actualizar sale de
    request.user, igual que SolicitanteUserSolicitanteView. Antes tomaba el
    email de la URL, así que cualquier solicitante autenticado podía pisar
    los datos de OTRO usuario con solo cambiar el email en la ruta —
    IsSolicitante solo exige "algún solicitante autenticado", no que
    coincida con el dueño del registro que se está modificando."""

    def put(self, request, format=None):
        services.actualizar_datos_usuario(request.user.email, request.data, request.FILES)
        return Response(status=200)


class VerificarProveedorSolicitanteView(SolicitanteAPIView):
    """Verifica un QR de proveedor escaneado (ver `QrTokenProveedorView` del
    lado proveedor). El token trae el id firmado con vencimiento — una
    captura de pantalla vieja deja de servir sola, sin que nadie tenga que
    revocar nada a mano."""

    def post(self, request, format=None):
        ok, data = services.verificar_proveedor_por_token(request.data.get("token"))
        if not ok:
            return Response({"valido": False, "error": data}, status=400)
        return Response({"valido": True, "proveedor": data})


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
    """Perfil propio del solicitante autenticado (login/registro/perfil).
    La identidad sale del token, no de un parámetro en la URL — evita que
    cualquier solicitante autenticado pueda pedir el perfil de otro solo
    cambiando el correo en la ruta. Comparte serializer con Admin (ver
    `SolicitanteUserAdminView`), que sí recibe el correo por parámetro
    porque ahí un admin consulta el perfil de otro usuario a propósito."""

    def get(self, request, format=None):
        serializer = SolicitanteSerializer(services.obtener_solicitante_por_email(request.user.email), many=True)
        data = serializer.data
        for solicitante in data:
            usuario = solicitante.get("user_datos", {}).get("user", {})
            usuario.pop("password", None)
            usuario.pop("groups", None)
            usuario.pop("is_superuser", None)
        return Response(data)


class ExisteEmailSolicitanteView(SolicitanteAPIView):
    """Público: chequeo de disponibilidad de correo antes de registrarse
    (register.page.ts), no puede exigir sesión previa."""

    permission_classes = [IsPublic]

    def get(self, request, email, format=None):
        existe = services.obtener_solicitante_por_email(email).exists()
        return Response({"existe": existe})


class DatosUsuarioSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (ver `DatosUsuarioProveedorView`) —
    feature de chat, mostrar datos básicos de la contraparte."""

    def get(self, request, id, format=None):
        from api.serializers import DatosContraparteSerializer

        serializer = DatosContraparteSerializer(services.obtener_datos_por_user_id(id), many=True)
        return Response(serializer.data)


class CompleteDataUserSolicitanteView(SolicitanteAPIView):
    """Endpoint compartido con Proveedor (ver `CompleteDataUserProveedorView`)."""

    def put(self, request, username, format=None):
        return Response(services.completar_datos_usuario(username, request.data))


class RecuperarPasswordSolicitanteView(SolicitanteAPIView):
    """Confirma el correo y le manda el enlace de cambio de contraseña (ver
    `RecuperarPasswordProveedorView`, el espejo de la app de proveedor).
    Público (IsPublic): pre-login."""

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
    """Sin `<email>` en la URL a propósito: los puntos que devuelve son
    siempre los de request.user, nunca los de un email pasado por parámetro
    (antes cualquier solicitante autenticado podía consultar el saldo de
    puntos de OTRO usuario con solo cambiar el email en la ruta)."""

    def get(self, request, format=None):
        return Response(services.obtener_puntos(request.user.email))


class CanjearInvitacionSolicitanteView(SolicitanteAPIView):
    """Sin `<email>` en la URL a propósito: el invitado que canjea el código
    es siempre request.user (antes cualquier solicitante autenticado podía
    canjear un código de invitación EN NOMBRE de otro usuario con solo
    cambiar el email en la ruta, gastando su cupo de "una vez por cuenta" y
    otorgándole los +10 puntos a esa cuenta ajena)."""

    def put(self, request, format=None):
        data = services.canjear_codigo_invitacion(request.user.email, request.data.get("codigo"))
        return Response(data)


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
