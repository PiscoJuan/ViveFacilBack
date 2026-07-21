from rest_framework.response import Response

from api.serializers import CategoriaSerializer, CiudadSerializer, Profesion_ProveedorSerializer, ServicioSerializer
from catalog import services
from core.views import SolicitanteAPIView


class ProveedoresPorServicioSolicitanteView(SolicitanteAPIView):
    def get(self, request, servicio_id, format=None):
        try:
            serializer = Profesion_ProveedorSerializer(
                services.proveedores_activos_por_servicio(servicio_id), many=True
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        return Response(serializer.data)


class CategoriasSolicitanteView(SolicitanteAPIView):
    """Endpoint propio del solicitante para listar categorías — antes no
    existía ninguna ruta pública, `CategoriasAdminView` es admin-exclusivo
    a propósito (ver su docstring)."""

    def get(self, request, format=None):
        return Response(CategoriaSerializer(services.listar_categorias(), many=True).data)


class ServiciosSolicitanteView(SolicitanteAPIView):
    """Endpoint propio del solicitante para listar servicios — antes pedía
    directo a `web/catalog/servicios/` (catalog.api.web.views.ServiciosWebView)."""

    def get(self, request, format=None):
        todas = request.GET.get("todas")
        return Response(ServicioSerializer(services.list_servicios(todas=bool(todas)), many=True).data)


class CiudadesSolicitanteView(SolicitanteAPIView):
    """Endpoint propio del solicitante para listar ciudades — antes pedía
    una ruta sin ningún prefijo de rol."""

    def get(self, request, format=None):
        return Response(CiudadSerializer(services.listar_ciudades(), many=True).data)
