import random

from django.conf import settings
from django.core.mail import send_mail

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
