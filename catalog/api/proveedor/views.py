from rest_framework.response import Response

from catalog import services
from core.views import ProveedorAPIView


class MisProfesionesProveedorView(ProveedorAPIView):
    """Réplica del GET de Proveedor_Profesiones (api/views.py:2983). El
    POST y el PUT (`profesion_prov/<pk>`, usado por Admin) se quedan en la
    clase legacy sin tocar hasta la Fase 5 — ver catalog.services."""

    def get(self, request, format=None):
        return Response(services.listar_profesiones_proveedor(request.user))
