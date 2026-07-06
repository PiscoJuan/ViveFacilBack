from rest_framework import viewsets
from rest_framework.response import Response

from api.models import Datos
from api.serializers import DatosSerializer
from core.permissions import IsPublic
from core.views import WebAPIView
from accounts import services
from accounts.api.web.serializers import Proveedor_PendienteSerializer


class ProveedoresPendientesEmailWebView(WebAPIView):
    """Replica de Proveedores_Pendientes_Email (api/views.py:1644).
    Devuelve el registro de Proveedor_Pendiente activo para ese email, o el
    string "nuevo" si no existe uno — el frontend (ViveFacilWeb) compara el
    body contra 'nuevo' directamente, no cambiar el formato de respuesta."""

    def get(self, request, mail, format=None):
        pendiente = services.get_proveedor_pendiente_activo_por_email(mail)
        if not pendiente:
            return Response("nuevo")
        serializer = Proveedor_PendienteSerializer(pendiente)
        return Response(serializer.data)


class ProveedorPendienteWebView(WebAPIView):
    """Replica de Proveedor_Pendiente_Admin.post (api/views.py:1570) — es el
    formulario público "quiero ser proveedor" del sitio, a pesar del nombre
    viejo de la clase. ViveFacil_Admin2022 también le pega a esta misma URL
    pública para alta manual; se deja así a propósito, ver
    docs/refactor/04-fase-2-web.md."""

    def post(self, request, format=None):
        _, serializer = services.crear_proveedor_pendiente(request.data, request.FILES)
        return Response({"success": True, "serializer": serializer.data})


class RegistroWebView(viewsets.ModelViewSet):
    """Réplica de Registro (api/views.py:713), viewset DRF registrado bajo
    `registro/` vía router. Endpoint multi-rol confirmado por grep fresco:
    lo invocan ViveFacil_Solicitante2022 (alta real de Solicitante,
    `postRegistro`) y ViveFacil_Admin2022 (`pendientes.component.ts`, alta
    manual de un proveedor/solicitante aprobado). ViveFacil_Provedor2022
    define el mismo wrapper pero ningún componente lo invoca — su alta real
    no pasa por acá.

    No hereda de WebAPIView (es un ModelViewSet, no un APIView) pero declara
    `permission_classes` igual — `core/checks.py` solo inspecciona ese
    atributo, no la herencia. Antes no tenía permission_classes en absoluto
    (público por default de DRF, sin DEFAULT_PERMISSION_CLASSES en
    settings) — IsPublic preserva ese mismo comportamiento, explícito."""

    serializer_class = DatosSerializer
    queryset = Datos.objects.all()
    permission_classes = [IsPublic]

    def create(self, request, *args, **kwargs):
        data = services.crear_cuenta_registro(request.POST, request.FILES)
        return Response(data)


class ProveedorPublicoWebView(WebAPIView):
    """Réplica de Get_Proveedor (api/views.py:1330-1336). Sin evidencia de
    llamador real en ningún frontend ni indicio de a qué rol pertenece —
    lectura pública de un perfil de proveedor por id de `user_datos`, se
    registra bajo `web/` por descarte (no es exclusivo de ningún rol
    confirmado)."""

    def get(self, request, pk, format=None):
        return Response(services.obtener_proveedor_por_pk(pk))
