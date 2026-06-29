import graphene


class HealthStatusType(graphene.ObjectType):
    version = graphene.String(required=True)


class AuthPayloadType(graphene.ObjectType):
    access_token = graphene.String(required=True)
    refresh_token = graphene.String()


class MediaPayloadType(graphene.ObjectType):
    media_id = graphene.String(required=True)
    url = graphene.String(required=True)
    expires_in = graphene.Int(required=True)


class CacheTestPayloadType(graphene.ObjectType):
    source = graphene.String(required=True)
    computed_at = graphene.Float(required=True)
    payload = graphene.String(required=True)
    ttl = graphene.Int()
    remaining_ttl = graphene.Int()


class EventPayloadType(graphene.ObjectType):
    id = graphene.String(required=True)
    sqs_message_id = graphene.String(required=True)
    type = graphene.String(required=True)
    payload = graphene.JSONString()
    status = graphene.String(required=True)
    created_at = graphene.String(required=True)
    processed_at = graphene.String()


# ── Per-resolver response wrappers ─────────────────────────────────────────────


class HealthResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    data = graphene.Field(HealthStatusType)


class AuthResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    data = graphene.Field(AuthPayloadType)


class StringResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    data = graphene.String()


class MediaResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    data = graphene.Field(MediaPayloadType)


class CacheTestResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    data = graphene.Field(CacheTestPayloadType)


class BoolResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    data = graphene.Boolean()


class EventsResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)
    message = graphene.String(required=True)
    data = graphene.List(EventPayloadType)
