from rest_framework.response import Response

from api.serializers import CuentaSerializer, TarjetaSerializer
from payments import services
from core.views import ProveedorAPIView


class CuentaProveedorView(ProveedorAPIView):
    """Réplica de CuentaProveedor (api/views.py:2605). Sin evidencia de
    llamador real en ningún frontend — se migra igual por consistencia de
    namespace."""

    def get(self, request, proveedorID, format=None):
        serializer = CuentaSerializer(services.listar_cuentas_por_proveedor(proveedorID), many=True)
        return Response(serializer.data)


class TarjetaUserProveedorView(ProveedorAPIView):
    """Réplica de TarjetaUser.get (api/views.py:1665), cleanup post-Fase-5
    Bloque 3 — endpoint multi-rol, Provedor2022 solo usa el GET (lectura),
    ver TarjetaUserSolicitanteView para el DELETE (exclusivo solicitante)."""

    def get(self, request, identifier, format=None):
        return Response(TarjetaSerializer(services.list_tarjetas_por_usuario(identifier), many=True).data)
