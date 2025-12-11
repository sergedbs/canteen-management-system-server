from django.db import models

from apps.common.models import BaseModel


class WebhookSource(models.TextChoices):
    STRIPE = "stripe", "Stripe"


class WebhookStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class WebhookEvent(BaseModel):
    """
    Stores webhook events for idempotency and audit trail.
    Prevents duplicate processing of the same event.
    """

    event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=100)
    source = models.CharField(max_length=20, choices=WebhookSource.choices, default=WebhookSource.STRIPE)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=WebhookStatus.choices, default=WebhookStatus.PENDING)
    error_message = models.TextField(blank=True, null=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.source} • {self.event_type} • {self.status}"
