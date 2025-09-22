from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.authentication.serializers import RegisterSerializer, TokenWithRoleObtainPairSerializer

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


class MFASetupView(RetrieveAPIView):
    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MFARequestView(RetrieveAPIView):
    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MFAVerifyView(RetrieveAPIView):
    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MFADisableView(RetrieveAPIView):
    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
