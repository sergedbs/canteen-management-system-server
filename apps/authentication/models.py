import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Session(models.Model):
    """
    Represents a login session for a user (per device).
    Tied to refresh tokens and used for session management.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sessions")
    sid = models.CharField(max_length=64, unique=True)  # session identifier, put in JWT claim

    # Device & Location Info
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_label = models.CharField(max_length=100, blank=True)

    # Add: Device fingerprinting for security
    device_fingerprint = models.CharField(max_length=64, blank=True, help_text="Browser/device fingerprint hash")

    # Session Lifecycle
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    # Add: Revocation tracking
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ("user_logout", "User Logout"),
            ("admin_revoked", "Admin Revoked"),
            ("suspicious_activity", "Suspicious Activity"),
            ("password_changed", "Password Changed"),
            ("mfa_failed", "MFA Failed"),
            ("expired", "Session Expired"),
        ],
    )

    # Security Features
    mfa_passed = models.BooleanField(default=False)

    # Add: Security tracking
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    last_failed_attempt = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "auth_sessions"
        indexes = [
            models.Index(fields=["user", "is_revoked"]),
            models.Index(fields=["sid"]),
            models.Index(fields=["expires_at", "is_revoked"]),  # For cleanup queries
            models.Index(fields=["user", "created_at"]),  # For user session history
        ]

    def __str__(self):
        return f"{self.user.email} - {self.device_label or self.sid}"

    @property
    def is_active(self):
        """Check if session is currently active"""
        return (
            not self.is_revoked and self.expires_at > timezone.now() and self.mfa_passed  # Assuming MFA is required
        )

    @property
    def is_expired(self):
        """Check if session has expired"""
        return self.expires_at <= timezone.now()

    def revoke(self, reason="user_logout"):
        """Safely revoke the session"""
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.revocation_reason = reason
        self.save(update_fields=["is_revoked", "revoked_at", "revocation_reason"])

    def extend_expiry(self, hours=24):
        """Extend session expiry (for 'remember me' functionality)"""
        self.expires_at = timezone.now() + timedelta(hours=hours)
        self.save(update_fields=["expires_at"])

    def update_activity(self, ip_address=None):
        """Update last seen timestamp and IP if changed"""
        update_fields = ["last_seen_at"]
        if ip_address and ip_address != self.ip_address:
            self.ip_address = ip_address
            update_fields.append("ip_address")
        self.save(update_fields=update_fields)
