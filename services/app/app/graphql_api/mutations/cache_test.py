import graphene

from app.graphql_api.types import BoolResponse

_CACHE_KEY = "cache_test"


class ClearCache(graphene.Mutation):
    Output = BoolResponse

    def mutate(self, info):
        cache = info.context.get("cache")
        if cache is None:
            return BoolResponse(success=False, message="Redis not configured")
        deleted = cache.delete(_CACHE_KEY)
        return BoolResponse(success=True, message="ok", data=deleted)


class CacheTestMutations(graphene.ObjectType):
    clear_cache = ClearCache.Field()
