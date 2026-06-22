import pytest
from unittest.mock import MagicMock
from rest_framework_simplejwt.exceptions import TokenError

from app.graphql_api.utils import get_token_from_bearer, verify_access_token


def test_get_token_from_bearer_valid():
    token = get_token_from_bearer("Bearer mytoken123")
    assert token == "mytoken123"


def test_get_token_from_bearer_missing_header():
    with pytest.raises(ValueError):
        get_token_from_bearer("")


def test_get_token_from_bearer_no_bearer_prefix():
    with pytest.raises(ValueError):
        get_token_from_bearer("Token mytoken")


def test_get_token_from_bearer_only_bearer():
    with pytest.raises(ValueError):
        get_token_from_bearer("Bearer")


def test_verify_access_token_invalid_raises():
    with pytest.raises(ValueError):
        verify_access_token("not.a.valid.token")
