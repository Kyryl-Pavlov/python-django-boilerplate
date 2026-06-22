from unittest.mock import patch

import pytest

from app.models import Event


@pytest.mark.django_db
class TestPublish:
    def test_no_auth_returns_401(self, client):
        res = client.post("/api/v1/events", {"type": "test"}, format="json")
        assert res.status_code == 401

    def test_missing_type_returns_422(self, client, auth_headers):
        res = client.post("/api/v1/events", {}, format="json", **auth_headers)
        assert res.status_code == 422

    def test_success_returns_202_with_message_id(self, client, auth_headers):
        with patch("app.api.v1.views.events.send_event", return_value="msg-abc"):
            res = client.post(
                "/api/v1/events",
                {"type": "order.created", "payload": {"order_id": 1}},
                format="json",
                **auth_headers,
            )
        assert res.status_code == 202
        assert res.json()["data"]["message_id"] == "msg-abc"

    def test_sqs_failure_returns_500(self, client, auth_headers):
        with patch("app.api.v1.views.events.send_event", side_effect=Exception("SQS down")):
            res = client.post(
                "/api/v1/events",
                {"type": "test.event"},
                format="json",
                **auth_headers,
            )
        assert res.status_code == 500


@pytest.mark.django_db
class TestList:
    def test_no_auth_returns_401(self, client):
        assert client.get("/api/v1/events").status_code == 401

    def test_empty_returns_empty_list(self, client, auth_headers):
        res = client.get("/api/v1/events", **auth_headers)
        assert res.status_code == 200
        assert res.json()["data"] == []

    def test_returns_stored_events(self, client, auth_headers):
        Event.objects.create(sqs_message_id="msg-001", type="user.created", status="processed")

        res = client.get("/api/v1/events", **auth_headers)
        data = res.json()["data"]
        assert len(data) == 1
        assert data[0]["sqs_message_id"] == "msg-001"
        assert data[0]["type"] == "user.created"
        assert data[0]["status"] == "processed"

    def test_response_contains_required_fields(self, client, auth_headers):
        Event.objects.create(sqs_message_id="msg-002", type="ping", status="processed")

        data = client.get("/api/v1/events", **auth_headers).json()["data"][0]
        assert {"id", "sqs_message_id", "type", "payload", "status", "created_at", "processed_at"} <= data.keys()
