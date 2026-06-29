import os

from django.conf import settings
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from app.api.utils import api_response
from app.models import Media
from app.services.aws_s3_service import get_presigned_url, upload_file

_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "pdf", "mp4", "mov"}


class MediaUploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return api_response(False, "No file provided", status_code=400)

        ext = os.path.splitext(file.name)[1].lstrip(".").lower()
        if ext not in _ALLOWED_EXTENSIONS:
            return api_response(False, f"File type '.{ext}' is not allowed", status_code=400)

        try:
            content_key = upload_file(file, str(request.user.id), file.name)
            url = get_presigned_url(content_key)
        except Exception as e:
            return api_response(False, f"Upload failed: {e}", status_code=500)

        media = Media.objects.create(user=request.user, content_key=content_key)

        return api_response(
            True,
            "File uploaded",
            data={
                "media_id": str(media.id),
                "url": url,
                "expires_in": settings.PRESIGNED_URL_EXPIRY,
            },
            status_code=201,
        )


class MediaUrlView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, media_id):
        try:
            media = Media.objects.get(id=media_id, user=request.user)
        except Media.DoesNotExist:
            return api_response(False, "Media not found", status_code=404)

        try:
            url = get_presigned_url(media.content_key)
        except Exception as e:
            return api_response(False, f"Could not generate URL: {e}", status_code=500)

        return api_response(True, "ok", data={"url": url})
