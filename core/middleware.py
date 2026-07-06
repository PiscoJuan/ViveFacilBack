import logging

logger = logging.getLogger("core.legacy_routes")


class LegacyRouteLoggingMiddleware:
    """Loguea cada request que termina resolviendo a una vista servida por
    `api.urls` (el namespace legacy). Sirve para confirmar tráfico cero en
    una ruta vieja antes de borrarla en las Fases 2-6 — ver
    docs/refactor/01-arquitectura-objetivo.md#7."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        resolver_match = getattr(request, "resolver_match", None)
        app_name = getattr(view_func, "__module__", "") if resolver_match else ""
        if app_name.startswith("api."):
            logger.info(
                "legacy_route_hit",
                extra={"path": request.path, "method": request.method},
            )
        return None
