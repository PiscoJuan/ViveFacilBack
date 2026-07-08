from rest_framework import status
from rest_framework.response import Response

from api.serializers import (
    CargoSerializer,
    InsigniaSerializer,
    MedallaSerializer,
    PoliticasSerializer,
    PublicidadSerializer,
    SuggestionSerializer,
)
from content import services
from core.pagination import MyCustomPagination, MyPaginationMixin
from core.views import AdminAPIView


class InsigniasListAdminView(AdminAPIView):
    """Ruta base `admin/content/insignias/` (GET+POST) — antes Admin2022 la
    pedía en `web/catalog/insignias/` (misma lógica que
    content.api.web.views.InsigniasWebView)."""

    def get(self, request, format=None):
        from content.models import Insignia
        return Response(InsigniaSerializer(Insignia.objects.all().filter(), many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_insignia(request.POST, request.FILES))


class PoliticasAdminView(AdminAPIView):
    """Ruta propia del admin para políticas — antes Admin2022 pedía directo
    a `web/content/politicas/` (content.api.web.views.PoliticasWebView)."""

    def get(self, request, format=None):
        return Response(PoliticasSerializer(services.list_politicas(), many=True).data)

    def put(self, request, identifier, format=None):
        from django.core.exceptions import ObjectDoesNotExist
        try:
            politica = services.actualizar_politica(identifier, request.data.get('terminos'))
        except ObjectDoesNotExist:
            return Response({"error": "Política no encontrada."}, status=404)
        return Response({'politics': PoliticasSerializer(politica).data})


class InsigniasAdminView(AdminAPIView):
    """El GET (lista
    completa) y el POST (comparten la URL `insignias/` con el GET) se
    quedan en la clase legacy — GET lo consumen también Provedor2022 y
    Solicitante2022 (grep confirmado), así que no puede exigir rol admin; el
    POST ahora delega a `content.services.crear_insignia` con
    `get_permissions()` endurecido (antes totalmente abierto, sin ningún
    permission_classes).

    Nota: el `put`/`delete` originales de `Insignias` (`id` por URL) nunca
    estuvieron wireados a ningún path en `api/urls.py` — eran código
    muerto. Se les da una URL real acá (`admin/content/insignias/<id>/`)
    en vez de perpetuar el bug de falta de wiring."""

    def put(self, request, id, format=None):
        data, valido = services.actualizar_insignia(id, request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        services.eliminar_insignia(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class InsigniaDetailsAdminView(AdminAPIView):
    """El GET (`insignias/
    <pk>`) y el PUT de estado (`insignia_estado/`, sin pk en la URL, por
    query param) se registran en paths separados — ver urls.py."""

    def get(self, request, pk, format=None):
        return Response(InsigniaSerializer(services.obtener_insignia(pk)).data)

    def put(self, request, format=None):
        services.actualizar_estado_insignia(request.GET.get("id"), request.data.get("estado"))
        return Response(status=status.HTTP_200_OK)


class MedallasAdminView(AdminAPIView):
    """Todo el CRUD, incluido el
    GET: sin evidencia de consumidor fuera del panel admin (a diferencia de
    Insignias)."""

    def get(self, request, format=None):
        return Response(MedallaSerializer(services.list_medallas(), many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_medalla(request.POST, request.FILES))

    def put(self, request, id, format=None):
        data, valido = services.actualizar_medalla(id, request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        services.eliminar_medalla(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MedallaEstadoAdminView(AdminAPIView):
    """Toggle de estado. No tiene GET: la clase legacy análoga tenía uno,
    pero nunca estuvo wireado a ninguna URL y además tenía un bug de
    copy-paste (consultaba Insignia en vez de Medalla) — código muerto, no
    se replica."""

    def put(self, request, format=None):
        services.actualizar_estado_medalla(request.GET.get("id"))
        return Response(status=status.HTTP_200_OK)


class CargosAdminView(AdminAPIView):
    def get(self, request, format=None):
        return Response(CargoSerializer(services.list_cargos(), many=True).data)

    def post(self, request, format=None):
        return Response(services.crear_cargo(
            request.POST.get("nombre"), request.POST.get("titulo"),
            request.POST.get("porcentaje"), request.POST.get("tipo"),
        ))

    def put(self, request, id, format=None):
        data, valido = services.actualizar_cargo(id, request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        services.eliminar_cargo(id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CargoDetailsAdminView(AdminAPIView):
    """No tiene PUT."""

    def get(self, request, pk, format=None):
        return Response(CargoSerializer(services.obtener_cargo(pk)).data)


class PublicidadesAdminView(AdminAPIView, MyPaginationMixin):
    """Admin-exclusivo, solo Admin2022 lo consume."""

    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.list_publicidades())
        if page is not None:
            return self.get_paginated_response(PublicidadSerializer(page, many=True).data)

    def post(self, request, format=None):
        data, valido = services.crear_publicidad(request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data, status=status.HTTP_201_CREATED)

    def put(self, request, format=None):
        data, valido = services.actualizar_publicidad(request.data.get("id"), request.data)
        if not valido:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        return Response(data)

    def delete(self, request, id, format=None):
        return Response(services.eliminar_publicidad(id))


class PublicidadesBuscarAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.buscar_publicidades(request.GET.get("buscar")))
        if page is not None:
            return self.get_paginated_response(PublicidadSerializer(page, many=True).data)


class ReadSuggestionsAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.list_sugerencias_leidas())
        if page is not None:
            return self.get_paginated_response(SuggestionSerializer(page, many=True).data)


class UnreadSuggestionsAdminView(AdminAPIView, MyPaginationMixin):
    pagination_class = MyCustomPagination

    def get(self, request, format=None):
        page = self.paginate_queryset(services.list_sugerencias_no_leidas())
        if page is not None:
            return self.get_paginated_response(SuggestionSerializer(page, many=True).data)


class SuggestionsDetalleAdminView(AdminAPIView):
    """Sirve dos alias de URL: `suggestion/<pk>` (GET, uso real por
    Admin2022) y `suggestion_estado/` (PUT, id por query param — ver
    `content.services.actualizar_estado_sugerencia` para el bug de 500
    real que esto corrige)."""

    def get(self, request, pk, format=None):
        return Response(SuggestionSerializer(services.obtener_sugerencia(pk)).data)

    def put(self, request, format=None):
        ok, _ = services.actualizar_estado_sugerencia(request.GET.get('id'), request.data.get('estado'))
        return Response(status=status.HTTP_200_OK if ok else status.HTTP_400_BAD_REQUEST)
