import pytest


@pytest.mark.django_db
def test_returns_ok_status(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["version"] is not None
