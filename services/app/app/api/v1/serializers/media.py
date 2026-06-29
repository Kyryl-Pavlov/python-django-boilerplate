from rest_framework import serializers


class MediaSerializer(serializers.Serializer):
    media_id = serializers.UUIDField()
    url = serializers.URLField()
    expires_in = serializers.IntegerField()
