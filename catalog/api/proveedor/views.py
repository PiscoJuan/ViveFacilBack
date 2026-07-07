from rest_framework.response import Response

from api.serializers import CiudadSerializer, Profesion_ProveedorSerializer, SolicitudProfesionSerializer
from catalog import services
from core.views import ProveedorAPIView


class CiudadesProveedorView(ProveedorAPIView):
    """Endpoint propio del proveedor para listar ciudades — antes pedía
    directo a `web/catalog/ciudades/` (catalog.api.web.views.CiudadesWebView)."""

    def get(self, request, format=None):
        return Response(CiudadSerializer(services.listar_ciudades(), many=True).data)


class SolicitudProfesionProveedorView(ProveedorAPIView):
    """El proveedor pide que se le agregue una profesión al perfil (con años
    de experiencia y evidencia en archivo); el admin la revisa vía
    catalog.api.admin.views.ManejoSolicitudAdminView (put/delete de
    `admin/catalog/solicitudes-profesion/gestion/<pk>/`)."""

    def post(self, request, format=None):
        data, solicitud = services.crear_solicitud_profesion(
            request.data.get("proveedor"), request.data.get("profesion"),
            request.data.get("anio"), request.FILES.get("documento"),
        )
        if solicitud is not None:
            return Response(SolicitudProfesionSerializer(solicitud).data)
        return Response(data)


class MisProfesionesProveedorView(ProveedorAPIView):
    """El PUT/DELETE (`profesion_prov/<pk>`, usado por Admin) tienen su
    propio hogar en catalog.api.admin.views.ProfesionProveedorDetalleAdminView."""

    def get(self, request, format=None):
        return Response(services.listar_profesiones_proveedor(request.user))

    def post(self, request, format=None):
        data, creada = services.crear_profesion_proveedor(request.user, request.data)
        if creada is not None:
            data["profesion_proveedor"] = Profesion_ProveedorSerializer(creada).data
        return Response(data)
