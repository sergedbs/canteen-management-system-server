from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.authentication.serializers import (
    LoginSerializer,
    RefreshSerializer,
    RegisterSerializer,
)

User = get_user_model()

COOKIE_NAME = "refresh_token"
COOKIE_MAX_AGE = 14 * 24 * 3600  # 14 days


def cookie_opts(request=None):
    return {
        "path": "/",
        "samesite": "Lax",
        "secure": (request.is_secure() if request else not settings.DEBUG),
        "httponly": True,
        # "domain": ".ourdomain.com"
    }


def delete_cookie_opts():
    """Options for deleting cookies - more limited than set_cookie"""
    return {
        "path": "/",
        "samesite": "Lax",
        # "domain": ".ourdomain.com"
    }


def set_refresh_cookie(response, refresh_token, request):
    if refresh_token:
        response.set_cookie(
            COOKIE_NAME,
            refresh_token,
            max_age=COOKIE_MAX_AGE,
            **cookie_opts(request),
        )
        if hasattr(response, "data") and "refresh" in response.data:
            del response.data["refresh"]


class CsrfView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        get_token(request)
        return Response(status=204)


@extend_schema(
    responses={
        201: {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "access": {"type": "string"},
            },
        }
    }
)
class RegisterView(CreateAPIView):
    """
    Sign-up a user using a corporate *.utm.md email and password of min length 8.
    Returns email + access in the body and sets the refresh token as an HttpOnly cookie.
    """

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        set_refresh_cookie(response, response.data.get("refresh"), request)
        return response


class LoginView(TokenObtainPairView):
    """Login with email/password. Returns access token and sets refresh token as HttpOnly cookie."""

    serializer_class = LoginSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        set_refresh_cookie(response, response.data.get("refresh"), request)
        return super().finalize_response(request, response, *args, **kwargs)


@extend_schema(
    description="Refresh access token using refresh token from HttpOnly cookie.",
    request=None,
    responses={
        200: {"type": "object", "properties": {"access": {"type": "string", "description": "New access token"}}}
    },
    tags=["auth"],
)
# @method_decorator(csrf_protect, name="dispatch")
class RefreshView(TokenRefreshView):
    """Refresh access token using refresh token from HttpOnly cookie."""

    serializer_class = RefreshSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        set_refresh_cookie(response, response.data.get("refresh"), request)
        return super().finalize_response(request, response, *args, **kwargs)


# @method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        description="Blacklist the refresh token from cookie and clear the refresh_token cookie from browser.",
        request=None,
        responses={204: {"description": "Successfully logged out"}},
        tags=["auth"],
    )
    def post(self, request):
        refresh = request.COOKIES.get(COOKIE_NAME)

        if refresh:
            try:
                from rest_framework_simplejwt.tokens import RefreshToken

                token = RefreshToken(refresh)
                token.blacklist()
            except (InvalidToken, TokenError):
                pass  # logout as idempotent

        resp = Response(status=status.HTTP_204_NO_CONTENT)
        resp.delete_cookie(COOKIE_NAME, **delete_cookie_opts())
        return resp
