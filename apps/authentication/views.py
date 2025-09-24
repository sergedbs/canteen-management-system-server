from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
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
from apps.authentication.services import disable_mfa, request_mfa_code, setup_mfa, verify_mfa

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
        serializer.is_valid(raise_exception=True)
        data = setup_mfa(request.user, serializer.validated_data["mfa_type"])
        return Response(data)


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
        serializer.is_valid(raise_exception=True)
        data = request_mfa_code(serializer.validated_data["email"])
        return Response(data)


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
        serializer.is_valid(raise_exception=True)
        data = verify_mfa(serializer.validated_data["email"], serializer.validated_data["code"])
        return Response(data)


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
        serializer.is_valid(raise_exception=True)
        data = disable_mfa(request.user, serializer.validated_data["password"])
        return Response(data)
