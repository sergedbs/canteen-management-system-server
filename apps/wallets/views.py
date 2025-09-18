from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.permissions import IsOwnerOrAdmin
from apps.wallets.models import Balance
from apps.wallets.serializers import BalanceSerializer


# Wallet
class WalletView(generics.RetrieveAPIView):
    queryset = Balance.objects.select_related("user")
    serializer_class = BalanceSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    lookup_field = "user_id"

    def get_object(self):
        user_id = self.kwargs.get("user_id")
        return get_object_or_404(Balance, user__id=user_id)


class WalletDepositView(APIView):
    def post(self, request, user_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class WalletWithdrawView(APIView):
    def post(self, request, user_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


# Wallet Transactions
class WalletTransactionListView(APIView):
    def get(self, request, user_id):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class WalletTransactionDetailView(APIView):
    def get(self, request, user_id, pk):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
