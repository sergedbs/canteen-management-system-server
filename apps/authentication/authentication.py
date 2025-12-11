import json
import logging
import urllib.request

import jwt
from django.conf import settings
from jwt import PyJWTError
from jwt.algorithms import RSAAlgorithm
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from apps.authentication.services import upsert_microsoft_user
from apps.common.redis_client import redis_client

logger = logging.getLogger(__name__)

JWKS_CACHE_KEY = "microsoft:jwks"
JWKS_CACHE_TTL = 3600  # seconds


def _fetch_jwks(tenant_id: str = "common") -> dict:
    """Fetch Microsoft's JSON Web Key Set for token signature verification.

    For multi-tenant apps, use 'common' to get keys that work across all tenants.
    """
    cache_key = f"{JWKS_CACHE_KEY}:{tenant_id}"
    cached = redis_client.get(cache_key)
    if cached:
        try:
            return json.loads(cached)
        except json.JSONDecodeError:
            # fallthrough to refetch
            pass

    # Use 'common' for multi-tenant apps to get keys for all tenants
    url = f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 - trusted Microsoft URL
        body = resp.read()
        jwks = json.loads(body)

    redis_client.setex(cache_key, JWKS_CACHE_TTL, json.dumps(jwks))
    return jwks


def _get_public_key(token: str, tenant_id: str = "common") -> str | None:
    try:
        unverified_header = jwt.get_unverified_header(token)
    except PyJWTError:
        return None

    kid = unverified_header.get("kid")
    if not kid:
        return None

    jwks = _fetch_jwks(tenant_id)
    keys = jwks.get("keys", [])
    for key in keys:
        if key.get("kid") == kid:
            return RSAAlgorithm.from_jwk(json.dumps(key))
    return None


def _is_microsoft_issuer(issuer: str) -> bool:
    return issuer.startswith("https://login.microsoftonline.com/")


def _extract_tenant_from_issuer(issuer: str) -> str | None:
    """Extract tenant ID from Microsoft issuer URL.

    Example: https://login.microsoftonline.com/abcd1234-.../v2.0 -> abcd1234-...
    """
    if not _is_microsoft_issuer(issuer):
        return None
    # Format: https://login.microsoftonline.com/{tenant}/v2.0
    parts = issuer.replace("https://login.microsoftonline.com/", "").split("/")
    return parts[0] if parts else None


def _is_multi_tenant_config() -> bool:
    """Check if the app is configured for multi-tenant authentication."""
    return settings.MICROSOFT_TENANT_ID in ("common", "organizations", "consumers")


class MicrosoftBearerAuthentication(BaseAuthentication):
    """
    DRF authentication class that validates Microsoft access tokens (Bearer).

    It leaves existing JWT authentication untouched; only triggers when the token
    issuer is Microsoft.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None
        if len(auth) == 1:
            raise AuthenticationFailed("Invalid Authorization header. No credentials provided.")
        if len(auth) > 2:
            raise AuthenticationFailed("Invalid Authorization header. Token string should not contain spaces.")

        raw_token = auth[1].decode("utf-8")

        # Quick unverified decode to decide if this is a Microsoft token; if not, let other auth classes handle it.
        try:
            unverified_claims = jwt.decode(raw_token, options={"verify_signature": False})
        except PyJWTError:
            return None

        issuer = unverified_claims.get("iss", "")
        if not _is_microsoft_issuer(issuer):
            return None  # not Microsoft -> let other authenticators run

        # For multi-tenant apps, extract tenant from token and validate format only
        # For single-tenant apps, validate against configured tenant
        token_tenant = _extract_tenant_from_issuer(issuer)
        if not token_tenant:
            raise AuthenticationFailed("Invalid Microsoft token issuer format.")

        if _is_multi_tenant_config():
            # Multi-tenant: accept any valid Microsoft issuer, use token's tenant for JWKS
            expected_issuer = f"https://login.microsoftonline.com/{token_tenant}/v2.0"
            jwks_tenant = "common"  # Use common endpoint for multi-tenant key discovery
        else:
            # Single-tenant: validate against configured tenant
            expected_issuer = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/v2.0"
            jwks_tenant = settings.MICROSOFT_TENANT_ID

        audiences = [settings.MICROSOFT_CLIENT_ID]
        api_audience = getattr(settings, "MICROSOFT_API_AUDIENCE", "")
        if api_audience:
            audiences.append(api_audience)

        public_key = _get_public_key(raw_token, jwks_tenant)
        if not public_key:
            raise AuthenticationFailed("Unable to fetch Microsoft signing key.")

        try:
            claims = jwt.decode(
                raw_token,
                key=public_key,
                algorithms=["RS256"],
                audience=audiences,
                issuer=expected_issuer,
            )
        except PyJWTError as exc:
            logger.info("Microsoft token validation failed: %s", exc)
            raise AuthenticationFailed("Invalid Microsoft access token.") from exc

        email = claims.get("preferred_username") or claims.get("email")
        microsoft_id = claims.get("oid")
        first_name = claims.get("given_name", "")
        last_name = claims.get("family_name", "")

        user, _ = upsert_microsoft_user(
            email=email,
            microsoft_id=microsoft_id,
            first_name=first_name,
            last_name=last_name,
        )

        return user, raw_token
