from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.authentication.serializers import (
    CustomTokenObtainPairSerializer,
    MFABackupCodesRegenerateSerializer,
    MFADisableSerializer,
    MFASetupConfirmSerializer,
    MFASetupStartSerializer,
    MFAVerifySerializer,
    RefreshSerializer,
    RegisterSerializer,
)
from apps.authentication.services import (
    disable_mfa,
    handle_mfa_flow,
    regenerate_backup_codes,
    setup_mfa_confirm,
    setup_mfa_start,
    verify_mfa,
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
    """Set refresh token as httpOnly cookie and remove from response body."""
    if refresh_token:
        response.set_cookie(
            COOKIE_NAME,
            refresh_token,
            max_age=COOKIE_MAX_AGE,
            **cookie_opts(request),
        )
        # Remove refresh from response body
        if hasattr(response, "data") and "refresh" in response.data:
            del response.data["refresh"]


class CsrfView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        get_token(request)
        return Response(status=204)


class RegisterView(CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        set_refresh_cookie(response, response.data.get("refresh"), request)
        return response


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        mfa_payload = handle_mfa_flow(user)
        if mfa_payload:
            # MFA required - don't set cookies yet
            return Response(mfa_payload, status=status.HTTP_200_OK)

        # No MFA - set refresh cookie
        response = Response(serializer.validated_data, status=status.HTTP_200_OK)
        set_refresh_cookie(response, response.data.get("refresh"), request)
        return response


class MFASetupStartView(APIView):
    serializer_class = MFASetupStartSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = setup_mfa_start(request.user)
        return Response(data)


class MFASetupConfirmView(APIView):
    serializer_class = MFASetupConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = setup_mfa_confirm(request.user, serializer.validated_data["code"])
        return Response(data)


class MFABackupCodesRegenerateView(APIView):
    serializer_class = MFABackupCodesRegenerateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = regenerate_backup_codes(request.user, serializer.validated_data["password"])
        return Response(data)


class MFAVerifyView(APIView):
    permission_classes = [AllowAny]
    serializer_class = MFAVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = verify_mfa(serializer.validated_data["ticket"], serializer.validated_data["code"])

        # After successful MFA verification, set refresh cookie
        response = Response(data, status=status.HTTP_200_OK)
        set_refresh_cookie(response, data.get("refresh"), request)
        return response


class MFADisableView(APIView):
    serializer_class = MFADisableSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = disable_mfa(request.user, serializer.validated_data["password"])
        return Response(data)


class RefreshView(TokenRefreshView):
    serializer_class = RefreshSerializer

    def finalize_response(self, request, response, *args, **kwargs):
        set_refresh_cookie(response, response.data.get("refresh"), request)
        return super().finalize_response(request, response, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [AllowAny]

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
