from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer

User = get_user_model()


# Admin / Staff
class UsersView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def post(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UserDetailView(RetrieveAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "id"

    def patch(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def delete(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UserPasswordAdminView(APIView):
    def patch(self, request, id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UserBalanceView(APIView):
    def get(self, request, id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UserOrdersView(APIView):
    def get(self, request, id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UserTransactionsView(APIView):
    def get(self, request, id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UserByAccountNoView(APIView):
    def get(self, request, account_no):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


# Self Profile (aliases)
class MeView(RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MePasswordView(APIView):
    def patch(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MeBalanceView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MeOrdersView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class MeTransactionsView(APIView):
    def get(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
