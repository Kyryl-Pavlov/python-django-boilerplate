import time

from django.apps import apps


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        try:
            app_config = apps.get_app_config("app")
            if app_config.logger_adapter:
                from app.logging.logger import AppLogger

                app_config.logger_adapter.log(
                    "response",
                    level=AppLogger.Level.INFO,
                    data={
                        "method": request.method,
                        "path": request.path,
                        "status": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
        except Exception:
            pass

        return response
