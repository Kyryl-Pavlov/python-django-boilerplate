from rest_framework import serializers


class PublishEventSerializer(serializers.Serializer):
    type = serializers.CharField(max_length=100)
    payload = serializers.DictField(required=False, allow_null=True, default=None)


class EventSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    sqs_message_id = serializers.CharField()
    type = serializers.CharField()
    payload = serializers.JSONField(allow_null=True)
    status = serializers.CharField()
    created_at = serializers.DateTimeField()
    processed_at = serializers.DateTimeField(allow_null=True)
