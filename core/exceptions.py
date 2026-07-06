from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

from core.responses import error_response


class CustomAPIException(APIException):
    """Levantar esto (o cualquier excepción de DRF) desde services/controllers
    para propagar un error manejado — custom_exception_handler lo formatea."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Error"

    def __init__(self, detail=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail or self.default_detail)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = detail["detail"]
    else:
        message = detail

    return error_response(message=message, status_code=response.status_code)
