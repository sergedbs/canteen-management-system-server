from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.authentication.serializers import (
    CustomTokenObtainPairSerializer,
    EmailResendSerializer,
    EmailVerifySerializer,
    MFABackupCodesRegenerateSerializer,
    MFADisableSerializer,
    MFASetupConfirmSerializer,
    MFASetupStartSerializer,
    MFAVerifySerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshSerializer,
    RegisterSerializer,
)
from apps.authentication.services import (
    disable_mfa,
    handle_mfa_flow,
    regenerate_backup_codes,
    send_password_reset_email,
    send_verification_email,
    setup_mfa_confirm,
    setup_mfa_start,
    verify_mfa,
)
from apps.authentication.utils import verify_email_token, verify_password_reset_token

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

        # Send verification email
        user = User.objects.get(email=response.data["email"])
        send_verification_email(user)

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


class EmailVerifyView(APIView):
    permission_classes = [AllowAny]
    serializer_class = EmailVerifySerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user_id = verify_email_token(token)

        if not user_id:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            if not user.is_verified:
                user.is_verified = True
                user.save()
            return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class EmailResendView(APIView):
    permission_classes = [AllowAny]
    serializer_class = EmailResendSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            if user.is_verified:
                return Response({"message": "Email already verified"}, status=status.HTTP_400_BAD_REQUEST)

            send_verification_email(user)
            return Response({"message": "Verification email sent"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Don't reveal user existence
            return Response({"message": "Verification email sent"}, status=status.HTTP_200_OK)


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


class PasswordChangeView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()

        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
            send_password_reset_email(user)
        except User.DoesNotExist:
            pass  # Don't reveal user existence

        return Response({"message": "Password reset email sent if account exists."}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        user_id = verify_password_reset_token(token)

        if not user_id:
            return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"message": "Password reset successfully"}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)


# Microsoft OAuth: Frontend handles full flow via MSAL library.
# Backend validates Microsoft Bearer tokens via MicrosoftBearerAuthentication class.
# No views needed - tokens are validated automatically on protected endpoints.
