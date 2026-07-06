import json

from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView
from django.http import JsonResponse
from rest_framework.response import Response

from accounts import services
from api.serializers import SolicitanteSerializer
from api.versionamiento import VERSION_ANDROID_SOLICITANTE, VERSION_IOS_SOLICITANTE
from core.permissions import IsPublic
from core.views import SolicitanteAPIView


class LoginSolicitanteView(SolicitanteAPIView):
    """Vista delgada de AuthService para el rol Solicitante — reemplaza el
    branching manual `if tipo == 'Proveedor'/'Solicitante'` que hoy vive en
    `Login.post()` (api/views.py:4113). Ver docs/refactor/05-fase-3-solicitante.md.

    Un login no puede exigir estar ya autenticado, así que sobreescribe el
    permiso heredado de SolicitanteAPIView (IsSolicitante) por IsPublic —
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
    """Réplica del endpoint multi-rol CambioContrasenia (api/views.py:798).
    IMPORTANTE: exige token válido de Firebase, no requiere estar ya
    logueado como Solicitante en este backend — igual que Login, es un
    endpoint de recuperación de acceso. Se registra público (IsPublic),
    igual que la ruta legacy compartida con proveedor."""

    permission_classes = [IsPublic]

    def post(self, request, format=None):
        data, http_status = services.cambiar_contrasenia_firebase(
            request.data.get("token"), request.data.get("pass")
        )
        return Response(data, status=http_status)


class DispositivoNotificacionSolicitanteView(SolicitanteAPIView):
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


class DatoSolicitanteView(SolicitanteAPIView):
    """Réplica del PUT de Dato (api/views.py:2668), Fase 4. Endpoint
    multi-rol compartido con Proveedor (ver DatoProveedorView en
    accounts/api/proveedor/views.py) — no se había detectado como
    multi-rol en esta misma fase (Fase 3), se resuelve acá."""

    def put(self, request, user, format=None):
        services.actualizar_datos_usuario(user, request.data, request.FILES)
        return Response(status=200)


class TarjetaCvcSolicitanteView(SolicitanteAPIView):
    """Réplica de CardsAuth (api/views.py:230-297). Solo lo consume
    ViveFacil_Solicitante2022 (paymentez.service.ts) — no es multi-rol pese
    a estar en el mismo archivo que otros endpoints de accounts."""

    def get(self, request, format=None):
        token = request.GET.get("token")
        if token is None:
            return Response({"sucess": False, "message": "No existe token pasado por parametro"})
        return JsonResponse(services.buscar_cvc_tarjeta(token), safe=False)

    def post(self, request, format=None):
        body = json.loads(request.body)
        creado = services.guardar_cvc_tarjeta(body["token"], body["cvc"])
        return JsonResponse({"valid": "OK" if creado else "NO"}, safe=False)

    def delete(self, request, token, format=None):
        success, message = services.eliminar_cvc_tarjeta(token)
        return JsonResponse({"success": success, "message": message})


class RegistroRedesSolicitanteView(SolicitanteAPIView):
    """Réplica de RegistroFromRedes (api/views.py:682-710). Sin evidencia de
    llamador real en ningún frontend (grep fresco, cero resultados incluso
    a nivel de definición de wrapper) — se migra igual por consistencia.
    Público (IsPublic): es parte del flujo de registro vía red social, no
    puede exigir sesión previa."""

    permission_classes = [IsPublic]

    def post(self, request, user, format=None):
        data, http_status = services.registrar_desde_redes(user, request.data, request.FILES)
        return Response(data, status=http_status)


class FacebookLoginSolicitanteView(SocialLoginView):
    """Réplica de FacebookLogin (api/views.py:853-855). Confirmado real,
    exclusivo de Solicitante2022 (login.page.ts). Público (IsPublic): es
    login, no puede exigir sesión previa."""

    adapter_class = FacebookOAuth2Adapter
    permission_classes = [IsPublic]


class GoogleLoginSolicitanteView(SocialLoginView):
    """Réplica de GoogleLogin (api/views.py:857-858). Ídem FacebookLogin."""

    adapter_class = GoogleOAuth2Adapter
    permission_classes = [IsPublic]


class SolicitanteUserSolicitanteView(SolicitanteAPIView):
    """Réplica de SolicitanteUser.get (api/views.py:1639-1645), endpoint
    multi-rol (ver también SolicitanteUserAdminView en
    accounts/api/admin/views.py) — usado en login/registro/perfil propio."""

    def get(self, request, user, format=None):
        serializer = SolicitanteSerializer(services.obtener_solicitante_por_email(user), many=True)
        return Response(serializer.data)


class DatosUsuarioSolicitanteView(SolicitanteAPIView):
    """Réplica de Datos_Users.get (api/views.py:2221-2227), endpoint
    multi-rol compartido con Proveedor (ver DatosUsuarioProveedorView) —
    feature de chat, mostrar datos básicos de la contraparte."""

    def get(self, request, id, format=None):
        from api.serializers import DatosSerializer

        serializer = DatosSerializer(services.obtener_datos_por_user_id(id), many=True)
        return Response(serializer.data)


class CompleteDataUserSolicitanteView(SolicitanteAPIView):
    """Réplica de Complete_Data_User.put (api/views.py:2230-2252), endpoint
    multi-rol sin evidencia de llamador real (ver también
    CompleteDataUserProveedorView en accounts/api/proveedor/views.py)."""

    def put(self, request, username, format=None):
        return Response(services.completar_datos_usuario(username, request.data))


class RecuperarPasswordSolicitanteView(SolicitanteAPIView):
    """Réplica de RecuperarPassword.get (api/views.py:565-575). Confirmado
    real, exclusivo de Solicitante2022 (recuperar-contrasenia.page.ts) —
    Provedor2022 define el mismo wrapper pero su recuperación real usa
    Firebase directo (grep confirmado). Público (IsPublic): pre-login."""

    permission_classes = [IsPublic]

    def get(self, request, user_email, format=None):
        return Response({"success": services.recuperar_password_existe(user_email)})


class ValidarCodigoSolicitanteView(SolicitanteAPIView):
    """Réplica de ValidarCodigo.get (api/views.py:595-606). Mismo alcance
    real que RecuperarPasswordSolicitanteView."""

    permission_classes = [IsPublic]

    def get(self, request, email, codigo, format=None):
        return Response({"success": services.validar_codigo_recuperacion(email, codigo)})


class CambioPasswordCodigoSolicitanteView(SolicitanteAPIView):
    """Réplica de CambioPasswordCodigo.get (api/views.py:609-627). Sin
    evidencia de llamador real ni siquiera en Solicitante2022 (que sí usa
    las dos vistas anteriores del mismo flujo) — se migra igual por
    consistencia. Público (IsPublic): pre-login."""

    permission_classes = [IsPublic]

    def get(self, request, email, password, codigo, format=None):
        return Response({"success": services.cambiar_password_con_codigo(email, password, codigo)})


class PuntosSolicitanteView(SolicitanteAPIView):
    """Réplica de Puntos.get (api/views.py:2824-2835). Confirmado real,
    exclusivo de Solicitante2022 (perfil/promociones) — endurecimiento real,
    antes sin permission_classes (público)."""

    def get(self, request, email, format=None):
        return Response(services.obtener_puntos(email))


class VersionAndroidSolicitanteView(SolicitanteAPIView):
    """Réplica de VerionAndroidSolicitante (api/views.py:2918-2920), typo
    "Verion" original. Confirmado real (app.component.ts, se consulta al
    lanzar la app). Público (IsPublic), mismo criterio que su análogo de
    proveedor (VersionAndroidProveedorView)."""

    permission_classes = [IsPublic]

    def get(self, request):
        return Response(VERSION_ANDROID_SOLICITANTE)


class VersionIosSolicitanteView(SolicitanteAPIView):
    """Réplica de VerionIosSolicitante (api/views.py:2922-2924). Ídem."""

    permission_classes = [IsPublic]

    def get(self, request):
        return Response(VERSION_IOS_SOLICITANTE)
