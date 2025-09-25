from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.authentication.serializers import (
    MFABackupCodesRegenerateSerializer,
    MFADisableSerializer,
    MFASetupConfirmSerializer,
    MFASetupStartSerializer,
    MFAVerifySerializer,
    RegisterSerializer,
    TokenWithRoleObtainPairSerializer,
)
from apps.authentication.services import (
    disable_mfa,
    regenerate_backup_codes,
    setup_mfa_confirm,
    setup_mfa_start,
    verify_mfa,
)

User = get_user_model()


class RegisterView(CreateAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class TokenWithRoleObtainPairView(TokenObtainPairView):
    serializer_class = TokenWithRoleObtainPairSerializer


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
        return Response(data)


class MFADisableView(APIView):
    serializer_class = MFADisableSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = disable_mfa(request.user, serializer.validated_data["password"])
        return Response(data)
