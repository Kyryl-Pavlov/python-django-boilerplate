import time

from django.apps import apps
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from app.api.utils import api_response

_CACHE_KEY = "cache_test"
_CACHE_TTL = 60


def _get_cache():
    return apps.get_app_config("app").cache


class CachePingView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        cache = _get_cache()
        if cache is None:
            return api_response(False, "Redis not configured", status_code=503)
        status = "ok" if cache.ping() else "unavailable"
        return api_response(True, "ok", data={"redis": status})


class CacheTestView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        cache = _get_cache()
        if cache is None:
            return api_response(False, "Redis not configured", status_code=503)

        cached = cache.get(_CACHE_KEY)
        if cached:
            remaining = cache.ttl(_CACHE_KEY)
            return api_response(
                True,
                "ok",
                data={**cached, "source": "cache", "remaining_ttl": remaining},
            )

        payload = {
            "source": "computed",
            "computed_at": time.time(),
            "payload": "hello from cache",
            "ttl": _CACHE_TTL,
        }
        cache.set(_CACHE_KEY, payload, ttl=_CACHE_TTL)
        return api_response(True, "ok", data=payload)

    def delete(self, request):
        cache = _get_cache()
        if cache is None:
            return api_response(False, "Redis not configured", status_code=503)
        deleted = cache.delete(_CACHE_KEY)
        return api_response(True, "ok", data={"deleted": deleted})
