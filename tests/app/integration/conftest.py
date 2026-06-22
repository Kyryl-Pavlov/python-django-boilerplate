import json
from unittest.mock import MagicMock

import pytest
from django.apps import apps
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user(db, client):
    client.post(
        "/api/v1/auth/register",
        {"email": "user@example.com", "password": "Password123!"},
        format="json",
    )
    return {"email": "user@example.com", "password": "Password123!"}


@pytest.fixture
def access_token(client, registered_user):
    res = client.post("/api/v1/auth/login", registered_user, format="json")
    return res.json()["data"]["access_token"]


@pytest.fixture
def refresh_token(client, registered_user):
    res = client.post("/api/v1/auth/login", registered_user, format="json")
    return res.json()["data"]["refresh_token"]


@pytest.fixture
def auth_headers(access_token):
    return {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}


@pytest.fixture
def mock_cache():
    app_config = apps.get_app_config("app")
    original = app_config.cache
    m = MagicMock()
    app_config.cache = m
    yield m
    app_config.cache = original


@pytest.fixture
def gql(client):
    def _execute(query: str, variables: dict | None = None, headers: dict | None = None):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        kwargs = {"content_type": "application/json"}
        if headers:
            kwargs.update(headers)
        return client.post("/graphql", json.dumps(payload), **kwargs)

    return _execute


@pytest.fixture
def gql_auth_headers(client, registered_user, db):
    res = client.post(
        "/graphql",
        json.dumps(
            {
                "query": """
                    mutation($email: String!, $password: String!) {
                        login(email: $email, password: $password) {
                            data { accessToken refreshToken }
                        }
                    }
                """,
                "variables": registered_user,
            }
        ),
        content_type="application/json",
    )
    tokens = res.json()["data"]["login"]["data"]
    return {
        "access": {"HTTP_AUTHORIZATION": f"Bearer {tokens['accessToken']}"},
        "refresh": {"HTTP_AUTHORIZATION": f"Bearer {tokens['refreshToken']}"},
    }
