import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _require(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} environment variable is not set")
    return value


SECRET_KEY = _require("SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django_prometheus",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "corsheaders",
    "rest_framework",
    "graphene_django",
    "app",
]

MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "app.middleware.logging.RequestLoggingMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "app.urls"

WSGI_APPLICATION = "wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "postgres"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", "postgres"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

_database_url = os.getenv("DATABASE_URL")
if _database_url:
    import re

    _m = re.match(
        r"(?:postgresql|postgres)(?:\+\w+)?://([^:]+):([^@]+)@([^:/]+):?(\d*)/(.+)",
        _database_url,
    )
    if _m:
        DATABASES["default"].update(
            {
                "USER": _m.group(1),
                "PASSWORD": _m.group(2),
                "HOST": _m.group(3),
                "PORT": _m.group(4) or "5432",
                "NAME": _m.group(5),
            }
        )

AUTH_USER_MODEL = "app.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "EXCEPTION_HANDLER": "app.api.exceptions.custom_exception_handler",
    "UNAUTHENTICATED_USER": None,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": os.getenv("JWT_SECRET_KEY") or SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

GRAPHENE = {
    "SCHEMA": "app.graphql_api.schema.schema",
    "MIDDLEWARE": [],
}

GRAPHQL_INTROSPECTION = False

CORS_ALLOW_ALL_ORIGINS = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_API_VN = os.getenv("REST_API_VN", "1.0.0")
GRAPHQL_API_VN = os.getenv("GRAPHQL_API_VN", "1.0.0")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "media-bucket")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
AWS_S3_PUBLIC_ENDPOINT_URL = os.getenv("AWS_S3_PUBLIC_ENDPOINT_URL")
PRESIGNED_URL_EXPIRY = int(os.getenv("PRESIGNED_URL_EXPIRY", "86400"))
AWS_SQS_ENDPOINT_URL = os.getenv("AWS_SQS_ENDPOINT_URL")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

REDIS_URL = os.getenv("REDIS_URL")

SENTRY_DSN = os.getenv("SENTRY_DSN")
CLOUDWATCH_LOG_GROUP = os.getenv("CLOUDWATCH_LOG_GROUP")
CLOUDWATCH_STREAM_NAME = os.getenv("CLOUDWATCH_STREAM_NAME", "app")
CLOUDWATCH_ENDPOINT_URL = os.getenv("CLOUDWATCH_ENDPOINT_URL")
LOKI_URL = os.getenv("LOKI_URL")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
