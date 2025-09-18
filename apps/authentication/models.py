import uuid

from django.conf import settings
from django.db import models


class Session(models.Model):
    """
    Represents a login session for a user (per device).
    Tied to refresh tokens and used for session management.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    sid = models.CharField(max_length=64, unique=True)  # session identifier, put in JWT claim
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_label = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    mfa_passed = models.BooleanField(default=False)

    class Meta:
        db_table = "auth_sessions"
        indexes = [
            models.Index(fields=["user", "is_revoked"]),
            models.Index(fields=["sid"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.device_label or self.sid}"
