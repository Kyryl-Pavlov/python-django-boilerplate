import os

import graphene
from django.conf import settings
from graphene_file_upload.scalars import Upload

from app.graphql_api.types import MediaPayloadType, MediaResponse
from app.graphql_api.utils import get_token_from_bearer, verify_access_token
from app.models import Media, User
from app.services.aws_s3_service import get_presigned_url, upload_file

_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "mp4", "mov"}


class UploadFile(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    Output = MediaResponse

    def mutate(self, info, file):
        auth_header = info.context["request"].META.get("HTTP_AUTHORIZATION", "")
        try:
            token = get_token_from_bearer(auth_header)
            user_id = verify_access_token(token)
        except ValueError as e:
            return MediaResponse(success=False, message=str(e))

        ext = os.path.splitext(file.name)[1].lstrip(".").lower()
        if ext not in _ALLOWED_EXTENSIONS:
            return MediaResponse(success=False, message=f"File type '.{ext}' is not allowed")

        try:
            user = User.objects.get(id=user_id)
            content_key = upload_file(file, user_id, file.name)
            url = get_presigned_url(content_key)
        except Exception as e:
            return MediaResponse(success=False, message=f"Upload failed: {e}")

        media = Media.objects.create(user=user, content_key=content_key)
        return MediaResponse(
            success=True,
            message="File uploaded",
            data=MediaPayloadType(
                media_id=str(media.id),
                url=url,
                expires_in=settings.PRESIGNED_URL_EXPIRY,
            ),
        )


class MediaMutations(graphene.ObjectType):
    upload_file = UploadFile.Field()
