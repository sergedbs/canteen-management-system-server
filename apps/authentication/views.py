from django.conf import settings
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.authentication.serializers import (
    CookieTokenRefreshSerializer,
    RegisterSerializer,
    TokenWithRoleObtainPairSerializer,
)

User = get_user_model()


@extend_schema(
    responses={
        201: {
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"},
                "access": {"type": "string"},
                "refresh": {"type": "string"},
            },
        }
    }
)
class RegisterView(CreateAPIView):
    """
    Sign-up a user using a corporate *.utm.md email and password of min length 8
    """

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


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
class CookieRegisterView(RegisterView):
    """
    Sign-up a user using a corporate *.utm.md email and password of min length 8.
    Sets refresh token as httpOnly cookie.
    """

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.data.get("refresh"):
            cookie_max_age = 3600 * 24 * 14  # 14 days
            response.set_cookie(
                "refresh_token",
                response.data["refresh"],
                max_age=cookie_max_age,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
            )
            del response.data["refresh"]
        return response


class TokenWithRoleObtainPairView(TokenObtainPairView):
    serializer_class = TokenWithRoleObtainPairSerializer


class CookieTokenObtainPairView(TokenWithRoleObtainPairView):
    def finalize_response(self, request, response, *args, **kwargs):
        if response.data.get("refresh"):
            cookie_max_age = 3600 * 24 * 14  # 14 days
            response.set_cookie(
                "refresh_token",
                response.data["refresh"],
                max_age=cookie_max_age,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
            )
            del response.data["refresh"]
        return super().finalize_response(request, response, *args, **kwargs)


class CookieTokenRefreshView(TokenRefreshView):
    def finalize_response(self, request, response, *args, **kwargs):
        if response.data.get("refresh"):
            cookie_max_age = 3600 * 24 * 14  # 14 days
            response.set_cookie(
                "refresh_token",
                response.data["refresh"],
                max_age=cookie_max_age,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
            )
            del response.data["refresh"]
        return super().finalize_response(request, response, *args, **kwargs)

    serializer_class = CookieTokenRefreshSerializer
