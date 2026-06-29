import time

import graphene

from app.graphql_api.types import (
    CacheTestPayloadType,
    CacheTestResponse,
    StringResponse,
)

_CACHE_KEY = "cache_test"
_CACHE_TTL = 60


class CacheTestQuery(graphene.ObjectType):
    cache_ping = graphene.Field(StringResponse)
    cache_test = graphene.Field(CacheTestResponse)

    def resolve_cache_ping(self, info):
        cache = info.context.get("cache")
        if cache is None:
            return StringResponse(success=False, message="Redis not configured")
        status = "ok" if cache.ping() else "unavailable"
        return StringResponse(success=True, message="ok", data=status)

    def resolve_cache_test(self, info):
        cache = info.context.get("cache")
        if cache is None:
            return CacheTestResponse(success=False, message="Redis not configured")

        cached = cache.get(_CACHE_KEY)
        if cached:
            remaining = cache.ttl(_CACHE_KEY)
            return CacheTestResponse(
                success=True,
                message="ok",
                data=CacheTestPayloadType(
                    source="cache",
                    computed_at=cached["computed_at"],
                    payload=cached["payload"],
                    ttl=cached.get("ttl"),
                    remaining_ttl=remaining,
                ),
            )

        payload = {
            "source": "computed",
            "computed_at": time.time(),
            "payload": "hello from cache",
            "ttl": _CACHE_TTL,
        }
        cache.set(_CACHE_KEY, payload, ttl=_CACHE_TTL)
        return CacheTestResponse(
            success=True,
            message="ok",
            data=CacheTestPayloadType(
                source="computed",
                computed_at=payload["computed_at"],
                payload=payload["payload"],
                ttl=_CACHE_TTL,
            ),
        )
