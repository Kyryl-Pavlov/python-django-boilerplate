import uuid

from django.db import models


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sqs_message_id = models.CharField(max_length=256, unique=True, db_index=True)
    type = models.CharField(max_length=100)
    payload = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20)  # "processed" | "failed"
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "events"
