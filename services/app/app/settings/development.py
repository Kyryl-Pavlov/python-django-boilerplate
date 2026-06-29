from .base import *  # noqa: F401, F403

DEBUG = True
GRAPHQL_INTROSPECTION = True

GRAPHENE["MIDDLEWARE"] = []  # noqa: F405

LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
