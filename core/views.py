from rest_framework.views import APIView

from core.permissions import IsAdministrador, IsProveedor, IsSolicitante, IsPublic


class AdminAPIView(APIView):
    permission_classes = [IsAdministrador]


class ProveedorAPIView(APIView):
    permission_classes = [IsProveedor]


class SolicitanteAPIView(APIView):
    permission_classes = [IsSolicitante]


class WebAPIView(APIView):
    permission_classes = [IsPublic]
