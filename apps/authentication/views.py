import base64
import random
import secrets
from io import BytesIO

import pyotp
import qrcode
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.authentication.serializers import (
    MFADisableSerializer,
    MFARequestSerializer,
    MFASetupSerializer,
    MFAVerifySerializer,
    RegisterSerializer,
    TokenWithRoleObtainPairSerializer,
)
from apps.common.redis_client import redis_client

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


class TokenWithRoleObtainPairView(TokenObtainPairView):
    serializer_class = TokenWithRoleObtainPairSerializer


@extend_schema(
    summary="Setup MFA",
    description="Setup MFA for the authenticated user. Choose between email or TOTP (authenticator app).",
    request=MFASetupSerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "qr_code": {"type": "string", "description": "Base64 QR code (TOTP only)"},
                "backup_codes": {"type": "array", "items": {"type": "string"}},
            },
        }
    },
    tags=["authentication"],
)
class MFASetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFASetupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        mfa_type = serializer.validated_data["mfa_type"]

        if mfa_type == "email":
            user.mfa_enabled = True
            user.mfa_type = "email"
            user.mfa_secret = None
            user.save()

            return Response(
                {"message": "Email MFA enabled successfully", "backup_codes": self._generate_backup_codes(user)}
            )

        elif mfa_type == "totp":
            # Generate TOTP secret
            secret = pyotp.random_base32()
            user.mfa_secret = secret
            user.mfa_enabled = True
            user.mfa_type = "totp"
            user.save()

            # Generate QR code
            totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="UTM Canteen")

            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)

            qr_img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            qr_code_b64 = base64.b64encode(buffer.getvalue()).decode()

            return Response(
                {
                    "message": "TOTP MFA enabled successfully",
                    "qr_code": qr_code_b64,
                    "backup_codes": self._generate_backup_codes(user),
                }
            )

    def _generate_backup_codes(self, user):
        """Generate and store backup codes in Redis"""
        backup_codes = [secrets.token_hex(4).upper() for _ in range(8)]
        redis_client.setex(f"backup_codes:{user.id}", 86400 * 30, ",".join(backup_codes))  # 30 days
        return backup_codes


@extend_schema(
    summary="Request MFA code",
    description="Request MFA code via email (only for email MFA type).",
    request=MFARequestSerializer,
    responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    tags=["authentication"],
)
class MFARequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MFARequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user.mfa_enabled or user.mfa_type != "email":
            return Response({"error": "Email MFA not enabled for this user"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Store OTP in Redis with 5-minute expiration
        redis_client.setex(f"mfa_otp:{user.id}", 300, otp)

        # Send email
        send_mail(
            subject="UTM Canteen - MFA Code",
            message=f"Your MFA code is: {otp}\n\nThis code will expire in 5 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"message": "MFA code sent to your email"})


@extend_schema(
    summary="Verify MFA code",
    description="Verify MFA code for login completion.",
    request=MFAVerifySerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "access": {"type": "string"},
                "refresh": {"type": "string"},
                "message": {"type": "string"},
            },
        }
    },
    tags=["authentication"],
)
class MFAVerifyView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = MFAVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if not user.mfa_enabled:
            return Response({"error": "MFA not enabled for this user"}, status=status.HTTP_400_BAD_REQUEST)

        # Check backup codes first
        backup_codes = redis_client.get(f"backup_codes:{user.id}")
        if backup_codes and code.upper() in backup_codes.split(","):
            # Remove used backup code
            remaining_codes = [c for c in backup_codes.split(",") if c != code.upper()]
            if remaining_codes:
                redis_client.setex(f"backup_codes:{user.id}", 86400 * 30, ",".join(remaining_codes))
            else:
                redis_client.delete(f"backup_codes:{user.id}")

            # Generate tokens
            refresh = TokenWithRoleObtainPairSerializer.get_token(user)
            return Response(
                {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "message": "MFA verified successfully with backup code",
                }
            )

        # Verify based on MFA type
        if user.mfa_type == "email":
            stored_otp = redis_client.get(f"mfa_otp:{user.id}")
            if not stored_otp or stored_otp != code:
                return Response({"error": "Invalid or expired MFA code"}, status=status.HTTP_400_BAD_REQUEST)

            # Delete used OTP
            redis_client.delete(f"mfa_otp:{user.id}")

        elif user.mfa_type == "totp":
            totp = pyotp.TOTP(user.mfa_secret)
            if not totp.verify(code, valid_window=1):  # Allow 1 window tolerance (30 seconds)
                return Response({"error": "Invalid TOTP code"}, status=status.HTTP_400_BAD_REQUEST)

        # Generate tokens
        refresh = TokenWithRoleObtainPairSerializer.get_token(user)
        return Response(
            {"access": str(refresh.access_token), "refresh": str(refresh), "message": "MFA verified successfully"}
        )


@extend_schema(
    summary="Disable MFA",
    description="Disable MFA for the authenticated user.",
    request=MFADisableSerializer,
    responses={200: {"type": "object", "properties": {"message": {"type": "string"}}}},
    tags=["authentication"],
)
class MFADisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = MFADisableSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        password = serializer.validated_data["password"]

        if not user.check_password(password):
            return Response({"error": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)

        user.mfa_enabled = False
        user.mfa_type = None
        user.mfa_secret = None
        user.save()

        # Clean up Redis data
        redis_client.delete(f"backup_codes:{user.id}")
        redis_client.delete(f"mfa_otp:{user.id}")

        return Response({"message": "MFA disabled successfully"})
