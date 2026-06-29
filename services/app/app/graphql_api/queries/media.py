import graphene

from app.graphql_api.types import StringResponse
from app.graphql_api.utils import get_token_from_bearer, verify_access_token
from app.models import Media
from app.services.aws_s3_service import get_presigned_url


class MediaQuery(graphene.ObjectType):
    signed_url = graphene.Field(StringResponse, media_id=graphene.String(required=True))

    def resolve_signed_url(self, info, media_id):
        auth_header = info.context["request"].META.get("HTTP_AUTHORIZATION", "")
        try:
            token = get_token_from_bearer(auth_header)
            user_id = verify_access_token(token)
        except ValueError as e:
            return StringResponse(success=False, message=str(e))

        try:
            media = Media.objects.get(id=media_id, user_id=user_id)
        except Media.DoesNotExist:
            return StringResponse(success=False, message="Media not found")

        try:
            url = get_presigned_url(media.content_key)
        except Exception as e:
            return StringResponse(success=False, message=f"Could not generate URL: {e}")

        return StringResponse(success=True, message="ok", data=url)
