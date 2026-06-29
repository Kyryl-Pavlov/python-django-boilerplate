import graphene

from app.graphql_api.types import StringResponse
from app.graphql_api.utils import get_token_from_bearer, verify_access_token
from app.services.aws_sqs_service import send_event


class PublishEvent(graphene.Mutation):
    class Arguments:
        type = graphene.String(required=True)
        payload = graphene.JSONString()

    Output = StringResponse

    def mutate(self, info, type, payload=None):
        auth_header = info.context["request"].META.get("HTTP_AUTHORIZATION", "")
        try:
            token = get_token_from_bearer(auth_header)
            verify_access_token(token)
        except ValueError as e:
            return StringResponse(success=False, message=str(e))

        try:
            import json

            payload_dict = json.loads(payload) if isinstance(payload, str) else payload
            message_id = send_event(type, payload_dict)
        except Exception as e:
            return StringResponse(
                success=False, message=f"Failed to publish event: {e}"
            )

        return StringResponse(success=True, message="Event published", data=message_id)


class EventMutations(graphene.ObjectType):
    publish_event = PublishEvent.Field()
