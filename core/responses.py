from rest_framework import status
from rest_framework.response import Response


def ok_response(data=None, message="OK", status_code=status.HTTP_200_OK):
    return Response(
        {
            "status": "success",
            "statusCode": status_code,
            "message": message,
            "data": data,
        },
        status=status_code,
    )


def error_response(message="Error", status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {
            "status": "error",
            "statusCode": status_code,
            "error": message,
        },
        status=status_code,
    )
