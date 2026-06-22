from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from app.api.utils import api_response
from app.api.v1.serializers.events import EventSerializer, PublishEventSerializer
from app.models import Event
from app.services.aws_sqs_service import send_event


class EventsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        events = Event.objects.order_by("-created_at")[:100]
        serializer = EventSerializer(events, many=True)
        return api_response(True, "ok", data=serializer.data)

    def post(self, request):
        serializer = PublishEventSerializer(data=request.data)
        if not serializer.is_valid():
            return api_response(False, "Invalid input", status_code=422)

        event_type = serializer.validated_data["type"]
        payload = serializer.validated_data.get("payload")

        try:
            message_id = send_event(event_type, payload)
        except Exception as e:
            return api_response(False, f"Failed to publish event: {e}", status_code=500)

        return api_response(
            True,
            "Event published",
            data={"message_id": message_id},
            status_code=202,
        )
