from rest_framework.response import Response


def api_response(success: bool, message: str, data=None, status_code: int = 200) -> Response:
    return Response(
        {
            "success": success,
            "message": message,
            "data": data,
            "status_code": status_code,
        },
        status=status_code,
    )
