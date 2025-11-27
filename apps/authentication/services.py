import base64
import json
import secrets
from io import BytesIO
from typing import TYPE_CHECKING

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions

from apps.authentication.crypto import decrypt_text, encrypt_text
from apps.authentication.models import MFABackupCode
from apps.authentication.utils import (
    generate_password_reset_token,
    generate_tokens_for_user,
    generate_verification_token,
)
from apps.common.redis_client import redis_client

if TYPE_CHECKING:
    from apps.users.models import User as UserType
else:
    UserType = object

User = get_user_model()


def send_verification_email(user: "UserType"):
    """Generate token and send verification email."""
    token = generate_verification_token(user)
    # TODO: Replace with actual frontend URL from settings  # noqa: FIX002
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    verification_link = f"{frontend_url}/verify-email?token={token}"

    send_mail(
        "Verify your email",
        f"Please click the following link to verify your email: {verification_link}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


def send_password_reset_email(user: "UserType"):
    """Generate token and send password reset email."""
    token = generate_password_reset_token(user)
    # Link points to frontend password reset page
    frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/reset-password?token={token}"

    send_mail(
        "Reset your password",
        f"Please click the following link to reset your password: {reset_link}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


def _to_str(val):
    if isinstance(val, bytes):
        return val.decode()
    return val


def _generate_backup_codes(user):
    """Generate backup codes, store hashed in DB, return plaintext list."""
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    # Invalidate existing codes
    user.mfa_backup_codes.all().delete()
    # Store hashed
    MFABackupCode.objects.bulk_create(
        [MFABackupCode(user=user, code_hash=make_password(code)) for code in backup_codes]
    )
    return backup_codes


def handle_mfa_flow(user):
    """
    If MFA is enabled, return MFA ticket and response payload.
    Otherwise return None.
    """
    if not user.mfa_enabled:
        return None

    # centralize ticket creation here
    ticket = create_mfa_ticket(user)
    return {
        "mfa_required": True,
        "mfa_type": user.mfa_type,
        "mfa_ticket": ticket,
        "message": "MFA verification required",
    }


def setup_mfa_start(user) -> dict:
    """Start MFA setup: generate secret, store encrypted pending secret, return QR + manual key."""
    secret = pyotp.random_base32()
    # store encrypted pending secret in Redis with TTL (15 minutes)
    enc_secret = encrypt_text(secret)
    redis_client.setex(f"mfa:setup:{user.id}", 900, enc_secret)

    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="UTM Canteen")

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()

    return {
        "message": "MFA setup started",
        "qr_code": qr_code_b64,
        "manual_key": secret,
        "issuer": "UTM Canteen",
        "account": user.email,
    }


def setup_mfa_confirm(user, code: str) -> dict:
    """Confirm MFA setup using the pending secret."""
    enc_secret = _to_str(redis_client.get(f"mfa:setup:{user.id}"))
    if not enc_secret:
        raise exceptions.ValidationError({"error": "No pending MFA setup or it has expired"})

    secret = decrypt_text(enc_secret)
    totp = pyotp.TOTP(secret)
    if not totp.verify(code, valid_window=1):
        raise exceptions.ValidationError({"error": "Invalid TOTP code"})

    # Persist encrypted secret on user and enable MFA
    user.mfa_secret = encrypt_text(secret)
    user.mfa_enabled = True
    user.mfa_type = "totp"
    user.save(update_fields=["mfa_secret", "mfa_enabled", "mfa_type"])

    # Clear pending secret
    redis_client.delete(f"mfa:setup:{user.id}")

    # Generate and return backup codes
    return {
        "message": "MFA setup confirmed",
        "backup_codes": _generate_backup_codes(user),
    }


def regenerate_backup_codes(user, password: str) -> dict:
    if not user.check_password(password):
        raise exceptions.ValidationError({"error": "Invalid password"})
    return {
        "message": "Backup codes regenerated",
        "backup_codes": _generate_backup_codes(user),
    }


def create_mfa_ticket(user, context: dict | None = None, ttl_seconds: int = 300) -> str:
    """Create a short-lived MFA ticket after primary auth (password) succeeds.

    Stores user id + optional context in Redis; returns opaque ticket.
    """
    ticket = secrets.token_urlsafe(32)
    # Ensure UUID or other non-JSON-serializable primary keys are stringified
    payload = {"user_id": str(user.id), "ctx": context or {}}
    redis_client.setex(f"mfa:pending:{ticket}", ttl_seconds, json.dumps(payload))
    return ticket


def verify_mfa(ticket: str, code: str) -> dict:
    # Retrieve pending ticket
    raw = redis_client.get(f"mfa:pending:{ticket}")
    if not raw:
        raise exceptions.ValidationError({"error": "Invalid or expired MFA ticket"})
    try:
        data = json.loads(_to_str(raw))
        user_id = data["user_id"]
    except (ValueError, KeyError) as err:  # corrupt payload -> treat as invalid
        redis_client.delete(f"mfa:pending:{ticket}")
        raise exceptions.ValidationError({"error": "Invalid or expired MFA ticket"}) from err

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist as err:
        redis_client.delete(f"mfa:pending:{ticket}")
        raise exceptions.ValidationError({"error": "Invalid or expired MFA ticket"}) from err

    if not user.mfa_enabled:
        redis_client.delete(f"mfa:pending:{ticket}")
        raise exceptions.ValidationError({"error": "MFA not enabled"})

    # Rate limit attempts per ticket
    attempts_key = f"mfa:attempts:{ticket}"
    attempts = redis_client.incr(attempts_key)
    if attempts == 1:
        # align attempts TTL with ticket TTL (best effort: 5 min)
        redis_client.expire(attempts_key, 300)
    if attempts > 5:
        redis_client.delete(f"mfa:pending:{ticket}")
        raise exceptions.ValidationError({"error": "Too many failed attempts"})

    # Backup codes (consume atomically)
    matched = False
    with transaction.atomic():
        qs = user.mfa_backup_codes.select_for_update().filter(used_at__isnull=True)
        for bc in qs:
            if check_password(code.upper(), bc.code_hash):
                bc.used_at = timezone.now()
                bc.save(update_fields=["used_at"])
                matched = True
                break

    if not matched:
        # TOTP path
        if user.mfa_type == "totp":
            secret = decrypt_text(user.mfa_secret)
            totp = pyotp.TOTP(secret)
            if not totp.verify(code, valid_window=1):
                raise exceptions.ValidationError({"error": "Invalid MFA code"})
        else:
            raise exceptions.ValidationError({"error": "Unsupported MFA type"})

    # Success -> clean up ticket & attempts
    redis_client.delete(f"mfa:pending:{ticket}")
    redis_client.delete(attempts_key)

    tokens = generate_tokens_for_user(user)
    return {
        **tokens,
        "message": "MFA verified successfully" if not matched else "MFA verified successfully with backup code",
    }


def disable_mfa(user, password: str) -> dict:
    if not user.check_password(password):
        raise exceptions.ValidationError({"error": "Invalid password"})

    user.mfa_enabled = False
    user.mfa_type = None
    user.mfa_secret = None
    user.save(update_fields=["mfa_enabled", "mfa_type", "mfa_secret"])

    user.mfa_backup_codes.all().delete()

    return {"message": "MFA disabled successfully"}
