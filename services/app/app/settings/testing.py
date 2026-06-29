import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-bytes!!!!")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-minimum-32-bytes!!")

from .base import *  # noqa: F401, F403, E402

DEBUG = True
TESTING = True
GRAPHQL_INTROSPECTION = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
