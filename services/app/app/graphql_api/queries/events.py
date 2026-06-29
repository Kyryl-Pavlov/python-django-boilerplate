import graphene

from app.graphql_api.types import EventPayloadType, EventsResponse
from app.graphql_api.utils import get_token_from_bearer, verify_access_token
from app.models import Event


def _event_to_payload(event):
    return EventPayloadType(
        id=str(event.id),
        sqs_message_id=event.sqs_message_id,
        type=event.type,
        payload=event.payload,
        status=event.status,
        created_at=event.created_at.isoformat(),
        processed_at=event.processed_at.isoformat() if event.processed_at else None,
    )


class EventsQuery(graphene.ObjectType):
    events = graphene.Field(EventsResponse)

    def resolve_events(self, info):
        auth_header = info.context["request"].META.get("HTTP_AUTHORIZATION", "")
        try:
            token = get_token_from_bearer(auth_header)
            verify_access_token(token)
        except ValueError as e:
            return EventsResponse(success=False, message=str(e))

        qs = Event.objects.order_by("-created_at")[:100]
        return EventsResponse(
            success=True,
            message="ok",
            data=[_event_to_payload(e) for e in qs],
        )
