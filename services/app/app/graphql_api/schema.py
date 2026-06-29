import graphene

from app.graphql_api.mutations.auth import AuthMutations
from app.graphql_api.mutations.cache_test import CacheTestMutations
from app.graphql_api.mutations.events import EventMutations
from app.graphql_api.mutations.media import MediaMutations
from app.graphql_api.queries.cache_test import CacheTestQuery
from app.graphql_api.queries.events import EventsQuery
from app.graphql_api.queries.health import HealthQuery
from app.graphql_api.queries.media import MediaQuery


class Query(HealthQuery, MediaQuery, EventsQuery, CacheTestQuery, graphene.ObjectType):
    pass


class Mutation(AuthMutations, MediaMutations, EventMutations, CacheTestMutations, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
