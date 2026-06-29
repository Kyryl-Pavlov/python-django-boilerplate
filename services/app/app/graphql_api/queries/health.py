import graphene
from django.conf import settings

from app.graphql_api.types import HealthResponse, HealthStatusType


class HealthQuery(graphene.ObjectType):
    health = graphene.Field(HealthResponse)

    def resolve_health(self, info):
        return HealthResponse(
            success=True,
            message="ok",
            data=HealthStatusType(version=settings.REST_API_VN),
        )
