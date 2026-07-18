import contextvars
import json
import logging
import os
import uuid
from datetime import datetime, timezone


_request_id_var = contextvars.ContextVar("request_id", default=None)


def get_request_id():
    return _request_id_var.get()


def set_request_id(value):
    _request_id_var.set(value)


def generate_request_id():
    # 32 chars, URL-safe, suficientemente único para trazabilidad
    return uuid.uuid4().hex


class RequestIdFilter:
    """Inyecta `request_id` en el LogRecord para usarlo en formatters."""

    def filter(self, record):  # logging.Filter signature
        record.request_id = get_request_id() or "-"
        return True


class ExtrasJsonFormatter(logging.Formatter):
    """Formatter JSON line para stdout (útil para grep/parseo en el error log de PythonAnywhere)."""

    _standard = {
        "name", "msg", "args", "message", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info", "lineno",
        "funcName", "created", "msecs", "relativeCreated", "thread",
        "threadName", "processName", "process", "taskName",
    }

    def format(self, record):
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        for k, v in record.__dict__.items():
            if k in self._standard or k == "request_id":
                continue
            log_data[k] = v

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        try:
            return json.dumps(log_data, ensure_ascii=False, default=str, separators=(",", ":"))
        except Exception:
            fallback = {k: str(v) for k, v in log_data.items()}
            return json.dumps(fallback, ensure_ascii=False, separators=(",", ":"))


class PrettyConsoleFormatter(logging.Formatter):
    """Formatter legible para desarrollo local."""

    _standard = ExtrasJsonFormatter._standard
    _reset = "\033[0m"
    _dim = "\033[2m"
    _colors = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35;1m",
    }
    _http_status_colors = {
        2: "\033[32m",
        3: "\033[36m",
        4: "\033[33m",
        5: "\033[31m",
    }

    def __init__(self, *args, use_colors=None, **kwargs):
        super().__init__(*args, **kwargs)
        if use_colors is None:
            use_colors = os.environ.get("NO_COLOR") is None
        self.use_colors = use_colors

    def _paint(self, value, color):
        if not self.use_colors:
            return value
        return f"{color}{value}{self._reset}"

    def _format_extra_value(self, key, value):
        rendered = f"{key}={value}"
        if not self.use_colors:
            return rendered

        if key != "status_code":
            return self._paint(rendered, self._dim)

        try:
            status_code = int(value)
        except (TypeError, ValueError):
            return rendered

        color = self._http_status_colors.get(status_code // 100)
        if not color:
            return rendered
        return self._paint(rendered, color)

    def format(self, record):
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone()
        level_text = f"{record.levelname:<8}"
        request_id = f"[{getattr(record, 'request_id', '-')}]"

        level_color = self._colors.get(record.levelname, "")
        if self.use_colors and level_color:
            level_text = self._paint(level_text, level_color)
            request_id = self._paint(request_id, self._dim)

        base = (
            f"{timestamp.strftime('%H:%M:%S')} "
            f"{level_text} "
            f"{request_id} "
            f"{record.name}: {record.getMessage()}"
        )

        extras = []
        for key, value in record.__dict__.items():
            if key in self._standard or key == "request_id":
                continue
            extras.append((key, value))

        if extras:
            ordered_extras = sorted(extras, key=lambda item: (item[0] != "status_code", item[0]))
            extras_text = " ".join(
                self._format_extra_value(key, value)
                for key, value in ordered_extras
            )
            base = f"{base} | {extras_text}"

        if record.exc_info:
            base = f"{base}\n{self.formatException(record.exc_info)}"

        return base
