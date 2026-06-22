import uuid

from django.db import models


class Media(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        "app.User",
        on_delete=models.CASCADE,
        related_name="media",
    )
    # S3 object key — not a URL; presigned URLs are generated on demand
    content_key = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "media"
