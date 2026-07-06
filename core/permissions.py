from rest_framework.permissions import BasePermission, AllowAny

from api.models import Datos  # hasta que la Fase 7 mueva el modelo


class BaseRolePermission(BasePermission):
    """Permiso de rol estructural: se fija en la vista base (AdminAPIView,
    etc.), no se llama a mano vista por vista. Ver docs/refactor/01-arquitectura-objetivo.md#5."""

    required_role = None  # "Proveedor" | "Solicitante" | "Administrador"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not hasattr(request, "_datos_cache"):
            request._datos_cache = Datos.objects.filter(user=request.user).first()
        datos = request._datos_cache
        return bool(datos and datos.tipo and datos.tipo.name == self.required_role)


class IsAdministrador(BaseRolePermission):
    required_role = "Administrador"


class IsProveedor(BaseRolePermission):
    required_role = "Proveedor"


class IsSolicitante(BaseRolePermission):
    required_role = "Solicitante"


class IsPublic(AllowAny):
    """AllowAny con otro nombre: declara explícitamente que un endpoint de
    `web/` es público a propósito, no por olvido."""
