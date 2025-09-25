import base64
import secrets
from io import BytesIO

import pyotp
import qrcode
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions

from apps.authentication.crypto import decrypt_text, encrypt_text
from apps.authentication.models import MFABackupCode
from apps.authentication.serializers import TokenWithRoleObtainPairSerializer
from apps.common.redis_client import redis_client

User = get_user_model()


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


def verify_mfa(email: str, code: str) -> dict:
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist as err:
        raise exceptions.NotFound({"error": "User not found"}) from err

    if not user.mfa_enabled:
        raise exceptions.ValidationError({"error": "MFA not enabled for this user"})

    # Backup codes (consume atomically to allow select_for_update)
    matched = False
    with transaction.atomic():
        qs = user.mfa_backup_codes.select_for_update().filter(used_at__isnull=True)
        for bc in qs:
            if check_password(code.upper(), bc.code_hash):
                bc.used_at = timezone.now()
                bc.save(update_fields=["used_at"])
                matched = True
                break

    if matched:
        refresh = TokenWithRoleObtainPairSerializer.get_token(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "message": "MFA verified successfully with backup code",
        }

    # TOTP only
    if user.mfa_type == "totp":
        secret = decrypt_text(user.mfa_secret)
        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            raise exceptions.ValidationError({"error": "Invalid TOTP code"})
    else:
        raise exceptions.ValidationError({"error": "Email-based MFA is no longer supported"})

    refresh = TokenWithRoleObtainPairSerializer.get_token(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh), "message": "MFA verified successfully"}


def disable_mfa(user, password: str) -> dict:
    if not user.check_password(password):
        raise exceptions.ValidationError({"error": "Invalid password"})

    user.mfa_enabled = False
    user.mfa_type = None
    user.mfa_secret = None
    user.save(update_fields=["mfa_enabled", "mfa_type", "mfa_secret"])

    user.mfa_backup_codes.all().delete()

    return {"message": "MFA disabled successfully"}
