from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        detail = response.data
        if isinstance(detail, dict) and "detail" in detail:
            message = str(detail["detail"])
        elif isinstance(detail, list):
            message = "; ".join(str(e) for e in detail)
        else:
            message = str(detail)
        response.data = {
            "success": False,
            "message": message,
            "data": None,
            "status_code": response.status_code,
        }
    return response
