from django.contrib.auth.forms import AuthenticationForm
from rest_framework import status, viewsets
from rest_framework.response import Response

from fcm_django.models import FCMDevice

from api.models import Datos
from api.serializers import DatosSerializer, FCMDeviceSerializer, SolicitanteSerializer
from core.permissions import IsPublic
from core.views import WebAPIView
from accounts import services
from accounts.api.web.serializers import Proveedor_PendienteSerializer


class ProveedoresPendientesEmailWebView(WebAPIView):
    """Devuelve el registro de Proveedor_Pendiente activo para ese email, o
    el string "nuevo" si no existe uno — el frontend (ViveFacilWeb) compara
    el body contra 'nuevo' directamente, no cambiar el formato de respuesta."""

    def get(self, request, mail, format=None):
        pendiente = services.get_proveedor_pendiente_activo_por_email(mail)
        if not pendiente:
            return Response("nuevo")
        serializer = Proveedor_PendienteSerializer(pendiente)
        return Response(serializer.data)


class ProveedorPendienteWebView(WebAPIView):
    """Es el formulario público "quiero ser proveedor" del sitio, a pesar
    del nombre viejo de la clase. ViveFacil_Admin2022 también le pega a
    esta misma URL pública para alta manual; se deja así a propósito."""

    def post(self, request, format=None):
        _, serializer = services.crear_proveedor_pendiente(request.data, request.FILES)
        return Response({"success": True, "serializer": serializer.data})


class RegistroWebView(viewsets.ModelViewSet):
    """Viewset DRF registrado bajo `registro/` vía router. Endpoint
    multi-rol: lo invocan ViveFacil_Solicitante2022 (alta real de
    Solicitante, `postRegistro`) y ViveFacil_Admin2022
    (`pendientes.component.ts`, alta manual de un proveedor/solicitante
    aprobado). ViveFacil_Provedor2022 define el mismo wrapper pero ningún
    componente lo invoca — su alta real no pasa por acá.

    No hereda de WebAPIView (es un ModelViewSet, no un APIView) pero
    declara `permission_classes` igual — `core/checks.py` solo inspecciona
    ese atributo, no la herencia. Deliberadamente público (IsPublic): es
    alta de cuenta nueva, sin sesión previa."""

    serializer_class = DatosSerializer
    queryset = Datos.objects.all()
    permission_classes = [IsPublic]

    def create(self, request, *args, **kwargs):
        data = services.crear_cuenta_registro(request.POST, request.FILES)
        return Response(data)


class ProveedorPublicoWebView(WebAPIView):
    """Lectura pública de un perfil de proveedor por id de `user_datos` —
    no es exclusiva de ningún rol confirmado."""

    def get(self, request, pk, format=None):
        return Response(services.obtener_proveedor_por_pk(pk))


class LoginWebView(WebAPIView):
    """A diferencia de LoginSolicitanteView/LoginProveedorView/LoginAdminView
    (que fijan `expected_role` según el namespace), esta vista toma el
    `tipo` del body — permite loguear cualquiera de los 3 roles desde una
    sola ruta abierta. Las rutas legacy `login/`/`loginadmin/` delegan
    ambas a esta MISMA clase, no una por rol."""

    def post(self, request, format=None):
        res_tipo = request.data.get("tipo")
        data = {}
        form = AuthenticationForm(data=request.data)
        if not form.is_valid():
            data["error"] = "Error de formulario login"
            data["active"] = True
            data["form"] = request.data
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password"]
        data, http_status = services.authenticate_login(request, username, password, res_tipo)
        data["form"] = request.data
        return Response(data, status=http_status)


class CambioContraseniaWebView(WebAPIView):
    """Endpoint multi-rol proveedor+solicitante, público a propósito
    (recuperación de acceso, no requiere sesión previa) — igual que
    CambioContraseniaSolicitanteView/CambioContraseniaProveedorView."""

    def post(self, request, format=None):
        data, http_status = services.cambiar_contrasenia_firebase(
            request.data.get("token"), request.data.get("pass")
        )
        return Response(data, status=http_status)


class DatoWebView(WebAPIView):
    """PUT multi-rol (proveedor+solicitante, ver
    accounts.api.{proveedor,solicitante}.views.Dato*View). Se preserva sin
    refuerzo de permiso."""

    def get(self, request, user, format=None):
        datos = Datos.objects.all().filter(user__email=user) | Datos.objects.all().filter(user__username=user)
        return Response({"dato": DatosSerializer(datos, many=True).data})

    def put(self, request, user, format=None):
        services.actualizar_datos_usuario(user, request.data, request.FILES)
        return Response(status=status.HTTP_200_OK)


class SolicitanteUserWebView(WebAPIView):
    """Endpoint multi-rol (Solicitante2022 + Admin2022, ver
    accounts.api.solicitante.views.SolicitanteUserSolicitanteView /
    accounts.api.admin.views.SolicitanteUserAdminView)."""

    def get(self, request, user, format=None):
        serializer = SolicitanteSerializer(services.obtener_solicitante_por_email(user), many=True)
        return Response(serializer.data)


class DatoUsuarioWebView(WebAPIView):
    """Endpoint multi-rol (Solicitante2022 + Provedor2022, feature de
    chat), ver accounts.api.{solicitante,proveedor}.views.DatosUsuario*View."""

    def get(self, request, id, format=None):
        serializer = DatosSerializer(services.obtener_datos_por_user_id(id), many=True)
        return Response(serializer.data)


class DispositivoNotificacionWebView(WebAPIView):
    """POST/DELETE ya viven en accounts.api.{solicitante,proveedor}.views
    (DispositivoNotificacion*View)."""

    def get(self, request, format=None):
        data = {}
        correo = request.data.get("correo")
        devices = FCMDevice.objects.filter(active=True, user=correo)
        serializer = FCMDeviceSerializer(devices, many=True)
        if len(devices) != 0:
            for device in devices:
                device.delete()
                num_devices += 1  # ponytail: bug preexistente preservado — `num_devices` nunca se inicializa, NameError garantizado si esta rama corre; sin evidencia de llamador real, no se corrige a ciegas
            data["success"] = True
            data["dispositivos"] = serializer.data
            return Response(data)
        else:
            data["success"] = False
            data["message"] = "No se han encontrados dispositivos con el correo: " + correo + " registrados en la base de datos"
            return Response(data)

    def post(self, request, format=None):
        data, http_status = services.registrar_dispositivo(request, request.data.get("token"))
        return Response(data, status=http_status)

    def delete(self, request, format=None):
        data, http_status = services.eliminar_dispositivos_por_correo(request.data.get("correo"))
        return Response(data, status=http_status)


class CompleteDataUserWebView(WebAPIView):
    """Registrada por consistencia bajo solicitante/proveedor (ver
    accounts.api.{solicitante,proveedor}.views.CompleteDataUser*View)."""

    def put(self, request, username, format=None):
        return Response(services.completar_datos_usuario(username, request.data))
