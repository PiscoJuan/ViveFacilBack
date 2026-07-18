import logging
from time import perf_counter

from django.utils.deprecation import MiddlewareMixin

from core.logging_context import generate_request_id, set_request_id

logger = logging.getLogger("http.access")


class RequestIdMiddleware(MiddlewareMixin):
    """
    - Acepta `X-Request-ID` si viene desde el cliente.
    - Genera uno si no viene.
    - Lo agrega al response como `X-Request-ID`.
    - Lo deja disponible para logging mediante ContextVar, así todos los
      logger.info/error(...) de un mismo request comparten el mismo id
      (útil para seguir el rastro de un request en el error log).
    """

    header_name = "HTTP_X_REQUEST_ID"  # request.META key
    response_header = "X-Request-ID"

    def process_request(self, request):
        incoming = request.META.get(self.header_name)
        request_id = incoming or generate_request_id()
        request.request_id = request_id
        set_request_id(request_id)

    def process_response(self, request, response):
        request_id = getattr(request, "request_id", None)
        if request_id:
            response[self.response_header] = request_id
        # Evita "contaminar" el ContextVar entre requests
        set_request_id(None)
        return response

    def process_exception(self, request, exception):
        # Asegura limpieza incluso en excepciones
        set_request_id(None)
        return None


class AccessLogMiddleware(MiddlewareMixin):
    """Access log estándar: una línea por request con método, path, status y duración."""

    timer_attr = "_access_log_started_at"
    logged_attr = "_access_log_written"

    def process_request(self, request):
        setattr(request, self.timer_attr, perf_counter())
        setattr(request, self.logged_attr, False)

    def process_response(self, request, response):
        if getattr(request, self.logged_attr, False):
            return response

        self._log_request(request, status_code=response.status_code)
        setattr(request, self.logged_attr, True)
        return response

    def process_exception(self, request, exception):
        if getattr(request, self.logged_attr, False):
            return None

        self._log_request(request, status_code=500)
        setattr(request, self.logged_attr, True)
        return None

    def _log_request(self, request, *, status_code):
        started_at = getattr(request, self.timer_attr, None)
        duration_ms = None
        if started_at is not None:
            duration_ms = round((perf_counter() - started_at) * 1000, 2)

        user = getattr(request, "user", None)
        is_authenticated = bool(getattr(user, "is_authenticated", False))
        username = getattr(user, "username", None) if is_authenticated else None
        user_id = getattr(user, "id", None) if is_authenticated else None

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
        remote_addr = x_forwarded_for.split(",")[0].strip() if x_forwarded_for else request.META.get("REMOTE_ADDR")

        extra = {
            "method": request.method,
            "path": request.get_full_path(),
            "status_code": status_code,
            "duration_ms": duration_ms,
            "remote_addr": remote_addr,
            "user_id": user_id,
            "username": username,
        }

        if status_code >= 500:
            logger.error("HTTP request completed", extra=extra)
            return
        if status_code >= 400:
            logger.warning("HTTP request completed", extra=extra)
            return
        logger.info("HTTP request completed", extra=extra)
