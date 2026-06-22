import pytest

pytestmark = pytest.mark.django_db


def test_returns_200_on_success(client):
    res = client.get("/api/v1/health")
    body = res.json()
    assert body["success"] is True
    assert body["status_code"] == 200


def test_response_envelope_has_required_keys(client):
    body = client.get("/api/v1/health").json()
    assert {"success", "message", "data", "status_code"} <= body.keys()


def test_success_false_on_404(client):
    res = client.get("/api/v1/media/00000000-0000-0000-0000-000000000000/url")
    assert res.status_code == 401
    body = res.json()
    assert body["success"] is False
