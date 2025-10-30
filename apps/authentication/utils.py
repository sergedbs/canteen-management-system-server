import random

from django.conf import settings
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.redis_client import redis_client

OTP_TTL = 300  # 5 minutes


def generate_email_otp(user):
    otp = str(random.randint(100000, 999999))
    key = f"otp:{user.id}"
    redis_client.setex(key, OTP_TTL, otp)

    send_mail(
        "Your OTP Code",
        f"Your verification code is {otp}. It expires in {OTP_TTL // 60} minutes.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    return otp


def verify_email_otp(user, token: str) -> bool:
    key = f"otp:{user.id}"
    otp = redis_client.get(key)
    if otp and otp == token:
        redis_client.delete(key)
        return True
    return False


def get_custom_token(user):
    """
    Return a refresh token with custom claims.
    """
    refresh = RefreshToken.for_user(user)
    refresh["role"] = user.role
    refresh["mfa_enabled"] = user.mfa_enabled
    refresh["verified"] = user.is_verified
    return refresh


def generate_tokens_for_user(user) -> dict:
    """
    Convenience function for access + refresh as strings.
    """
    refresh = get_custom_token(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
