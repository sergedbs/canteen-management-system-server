import base64
import random
import secrets
from io import BytesIO

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from rest_framework import exceptions

from apps.authentication.serializers import TokenWithRoleObtainPairSerializer
from apps.common.redis_client import redis_client

User = get_user_model()


def _to_str(val):
    if isinstance(val, bytes):
        return val.decode()
    return val


def _generate_backup_codes(user):
    """Generate and store backup codes in Redis for 30 days."""
    backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
    redis_client.setex(f"backup_codes:{user.id}", 86400 * 30, ",".join(backup_codes))  # 30 days
    return backup_codes


def setup_mfa(user, mfa_type: str) -> dict:
    if mfa_type == "email":
        user.mfa_enabled = True
        user.mfa_type = "email"
        user.mfa_secret = None
        user.save()
        return {"message": "Email MFA enabled successfully", "backup_codes": _generate_backup_codes(user)}

    if mfa_type == "totp":
        secret = pyotp.random_base32()
        user.mfa_secret = secret
        user.mfa_enabled = True
        user.mfa_type = "totp"
        user.save()

        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="UTM Canteen")

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()

        return {
            "message": "TOTP MFA enabled successfully",
            "qr_code": qr_code_b64,
            "backup_codes": _generate_backup_codes(user),
        }

    raise exceptions.ValidationError({"mfa_type": "Unsupported MFA type"})


def request_mfa_code(email: str) -> dict:
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist as err:
        raise exceptions.NotFound({"error": "User not found"}) from err

    if not user.mfa_enabled or user.mfa_type != "email":
        raise exceptions.ValidationError({"error": "Email MFA not enabled for this user"})

    otp = str(random.randint(100000, 999999))
    redis_client.setex(f"mfa_otp:{user.id}", 300, otp)

    send_mail(
        subject="UTM Canteen - MFA Code",
        message=f"Your MFA code is: {otp}\n\nThis code will expire in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return {"message": "MFA code sent to your email"}


def verify_mfa(email: str, code: str) -> dict:
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist as err:
        raise exceptions.NotFound({"error": "User not found"}) from err

    if not user.mfa_enabled:
        raise exceptions.ValidationError({"error": "MFA not enabled for this user"})

    # Backup codes
    backup_codes = _to_str(redis_client.get(f"backup_codes:{user.id}"))
    if backup_codes:
        codes_list = backup_codes.split(",")
        if code.upper() in codes_list:
            remaining = [c for c in codes_list if c != code.upper()]
            if remaining:
                redis_client.setex(f"backup_codes:{user.id}", 86400 * 30, ",".join(remaining))
            else:
                redis_client.delete(f"backup_codes:{user.id}")

            refresh = TokenWithRoleObtainPairSerializer.get_token(user)
            return {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "message": "MFA verified successfully with backup code",
            }

    # Email OTP
    if user.mfa_type == "email":
        stored_otp = _to_str(redis_client.get(f"mfa_otp:{user.id}"))
        if not stored_otp or stored_otp != code:
            raise exceptions.ValidationError({"error": "Invalid or expired MFA code"})
        redis_client.delete(f"mfa_otp:{user.id}")

    # TOTP
    elif user.mfa_type == "totp":
        totp = pyotp.TOTP(user.mfa_secret)
        if not totp.verify(code, valid_window=1):
            raise exceptions.ValidationError({"error": "Invalid TOTP code"})

    refresh = TokenWithRoleObtainPairSerializer.get_token(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh), "message": "MFA verified successfully"}


def disable_mfa(user, password: str) -> dict:
    if not user.check_password(password):
        raise exceptions.ValidationError({"error": "Invalid password"})

    user.mfa_enabled = False
    user.mfa_type = None
    user.mfa_secret = None
    user.save()

    redis_client.delete(f"backup_codes:{user.id}")
    redis_client.delete(f"mfa_otp:{user.id}")

    return {"message": "MFA disabled successfully"}
