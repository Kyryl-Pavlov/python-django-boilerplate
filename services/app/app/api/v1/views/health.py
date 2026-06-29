from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from app.api.utils import api_response


class HealthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        return api_response(
            success=True,
            message="ok",
            data={"version": settings.REST_API_VN},
        )
