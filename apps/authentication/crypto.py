from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _get_fernet() -> Fernet:
    key = getattr(settings, "MFA_FERNET_KEY", None)
    if not key:
        raise RuntimeError("MFA_FERNET_KEY is not configured")
    return Fernet(key)


def encrypt_text(value: str) -> str:
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_text(value: str) -> str:
    f = _get_fernet()
    try:
        return f.decrypt(value.encode()).decode()
    except InvalidToken as err:  # re-raise as ValueError to keep deps local
        raise ValueError("Invalid MFA secret token") from err
