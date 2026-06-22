import pytest

_QUERY = """
query {
    health {
        success
        message
        data { version }
    }
}
"""


@pytest.mark.django_db
def test_health_returns_success(gql):
    res = gql(_QUERY)
    assert res.status_code == 200
    payload = res.json()["data"]["health"]
    assert payload["success"] is True


@pytest.mark.django_db
def test_health_returns_version(gql):
    payload = gql(_QUERY).json()["data"]["health"]
    assert payload["data"]["version"] is not None


@pytest.mark.django_db
def test_health_returns_message(gql):
    payload = gql(_QUERY).json()["data"]["health"]
    assert payload["message"] != ""
