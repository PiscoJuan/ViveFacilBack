from rest_framework import serializers

from api.serializers import (
    CategoriaSerializer,
    CiudadSerializer,
    ProfesionSerializer,
    ServicioSerializer,
    SolicitudProfesionSerializer,
)
from catalog import services
from catalog.models import Servicio

__all__ = [
    "CategoriaSerializer",
    "CategoriaListAdminSerializer",
    "CiudadSerializer",
    "ProfesionSerializer",
    "ServicioSerializer",
    "ServicioListAdminSerializer",
    "SolicitudProfesionSerializer",
]


class CategoriaListAdminSerializer(CategoriaSerializer):
    """Solo para el listado admin de categorías: agrega el total de
    sub-categorías (Servicio) asociadas. No se usa en CategoriaSerializer
    base porque ese lo comparten otras vistas que no necesitan el conteo."""

    total_subcategorias = serializers.SerializerMethodField()

    class Meta(CategoriaSerializer.Meta):
        fields = CategoriaSerializer.Meta.fields + ['total_subcategorias']

    def get_total_subcategorias(self, obj):
        return Servicio.objects.filter(categoria=obj).count()


class ServicioListAdminSerializer(ServicioSerializer):
    """Solo para el listado admin de sub-categorías: agrega el total de
    proveedores asociados (ver catalog.services.profesion_proveedor_por_servicio).
    No se usa en ServicioSerializer base porque ese lo comparten las vistas
    públicas/solicitante, que no necesitan este conteo extra por fila."""

    total_proveedores = serializers.SerializerMethodField()

    class Meta(ServicioSerializer.Meta):
        fields = ServicioSerializer.Meta.fields + ['total_proveedores']

    def get_total_proveedores(self, obj):
        return services.profesion_proveedor_por_servicio(obj.id).count()
