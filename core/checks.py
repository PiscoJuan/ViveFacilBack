from django.core.checks import Error, register

from core.permissions import IsAdministrador, IsProveedor, IsSolicitante, IsPublic

ROLE_PERMISSION_BY_NAMESPACE = {
    "admin": IsAdministrador,
    "proveedor": IsProveedor,
    "solicitante": IsSolicitante,
    "web": IsPublic,
}


def _iter_view_classes(urlpatterns):
    for entry in urlpatterns:
        if hasattr(entry, "url_patterns"):
            yield from _iter_view_classes(entry.url_patterns)
        else:
            view_class = getattr(entry.callback, "cls", None)
            if view_class is not None:
                yield entry, view_class


@register()
def check_role_permissions(app_configs, **kwargs):
    """Falla `manage.py check` si una vista registrada bajo un namespace de
    rol (admin/proveedor/solicitante/web) no tiene la permission class que
    corresponde a ese rol entre sus `permission_classes`.

    Heredar de AdminAPIView/etc. en vez de APIView pelado para pasar este check."""
    errors = []
    for namespace, required_permission in ROLE_PERMISSION_BY_NAMESPACE.items():
        try:
            urlconf = __import__(f"core.urls.{namespace}", fromlist=["urlpatterns"])
        except ImportError:
            continue
        for entry, view_class in _iter_view_classes(urlconf.urlpatterns):
            permission_classes = getattr(view_class, "permission_classes", [])
            # IsPublic también vale bajo cualquier namespace: un endpoint
            # deliberadamente público anidado en un prefijo de rol (ej.
            # `solicitante/accounts/login/`, que no puede exigir estar
            # autenticado porque es el propio endpoint que autentica) declara
            # esa intención con IsPublic en vez de "olvidarse" del permiso.
            if not any(
                isinstance(p, type) and issubclass(p, (required_permission, IsPublic))
                for p in permission_classes
            ):
                errors.append(
                    Error(
                        f"{view_class.__module__}.{view_class.__name__} está "
                        f"registrada bajo el namespace '{namespace}/' pero no "
                        f"hereda el permiso {required_permission.__name__}.",
                        hint=(
                            "Heredar de la vista base del rol en core.views "
                            "(AdminAPIView/ProveedorAPIView/SolicitanteAPIView/"
                            "WebAPIView) en vez de APIView directo."
                        ),
                        obj=view_class,
                        id="core.E001",
                    )
                )
    return errors
