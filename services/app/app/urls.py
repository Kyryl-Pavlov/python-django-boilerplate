from django.conf import settings
from django.urls import include, path

from app.graphql_api.context import CustomGraphQLView
from app.graphql_api.schema import schema

urlpatterns = [
    path("api/v1/", include("app.api.v1.urls")),
    path(
        "graphql",
        CustomGraphQLView.as_view(graphiql=settings.DEBUG, schema=schema),
    ),
    path("", include("django_prometheus.urls")),
]
