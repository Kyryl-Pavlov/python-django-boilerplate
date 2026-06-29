from unittest.mock import patch

import pytest

from app.models import Event

_EVENTS = """
query {
    events {
        success
        message
        data { id sqsMessageId type status createdAt processedAt }
    }
}
"""

_PUBLISH = """
mutation($type: String!, $payload: JSONString) {
    publishEvent(type: $type, payload: $payload) {
        success
        message
        data
    }
}
"""


@pytest.mark.django_db
class TestEvents:
    def test_no_auth_returns_error(self, gql):
        payload = gql(_EVENTS).json()["data"]["events"]
        assert payload["success"] is False

    def test_empty_returns_empty_list(self, gql, gql_auth_headers):
        payload = gql(_EVENTS, headers=gql_auth_headers["access"]).json()["data"][
            "events"
        ]
        assert payload["success"] is True
        assert payload["data"] == []

    def test_returns_stored_events(self, gql, gql_auth_headers):
        Event.objects.create(
            sqs_message_id="msg-gql-01", type="gql.test", status="processed"
        )

        payload = gql(_EVENTS, headers=gql_auth_headers["access"]).json()["data"][
            "events"
        ]
        assert payload["success"] is True
        assert len(payload["data"]) == 1
        event = payload["data"][0]
        assert event["sqsMessageId"] == "msg-gql-01"
        assert event["type"] == "gql.test"
        assert event["status"] == "processed"
        assert event["createdAt"] is not None
        assert event["processedAt"] is None


@pytest.mark.django_db
class TestPublishEvent:
    def test_no_auth_returns_error(self, gql):
        payload = gql(_PUBLISH, {"type": "test"}).json()["data"]["publishEvent"]
        assert payload["success"] is False

    def test_success_returns_message_id(self, gql, gql_auth_headers):
        with patch(
            "app.graphql_api.mutations.events.send_event", return_value="msg-xyz"
        ):
            payload = gql(
                _PUBLISH,
                {"type": "order.placed"},
                headers=gql_auth_headers["access"],
            ).json()["data"]["publishEvent"]
        assert payload["success"] is True
        assert payload["data"] == "msg-xyz"

    def test_sqs_failure_returns_error(self, gql, gql_auth_headers):
        with patch(
            "app.graphql_api.mutations.events.send_event",
            side_effect=Exception("SQS down"),
        ):
            payload = gql(
                _PUBLISH, {"type": "test.event"}, headers=gql_auth_headers["access"]
            ).json()["data"]["publishEvent"]
        assert payload["success"] is False
        assert "Failed to publish" in payload["message"]
