from rest_framework.response import Response

from api.serializers import CuentaSerializer, TarjetaSerializer
from payments import services
from core.views import ProveedorAPIView


class CuentaProveedorView(ProveedorAPIView):
    """Sin evidencia de
    llamador real en ningún frontend — se migra igual por consistencia de
    namespace."""

    def get(self, request, proveedorID, format=None):
        serializer = CuentaSerializer(services.listar_cuentas_por_proveedor(proveedorID), many=True)
        return Response(serializer.data)


class TarjetaUserProveedorView(ProveedorAPIView):
    def get(self, request, identifier, format=None):
        return Response(TarjetaSerializer(services.list_tarjetas_por_usuario(identifier), many=True).data)
