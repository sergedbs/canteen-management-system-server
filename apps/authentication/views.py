from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny

from apps.authentication.serializers import RegisterSerializer

User = get_user_model()


class RegisterView(CreateAPIView):
    """
    Sign-up a user using a corporate *.utm.md email and password of min length 8
    """

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
