from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import PermissionMixin, VerifiedOwnerMixin
from apps.users.models import User
from apps.wallets.models import Balance, Transaction
from apps.wallets.serializers import (
    BalanceSerializer,
    DepositSerializer,
    TransactionPublicSerializer,
)


# Wallet
class WalletView(VerifiedOwnerMixin, generics.RetrieveAPIView):
    """Get a user's wallet balance. Users can only see their own balance, staff can see any balance."""

    serializer_class = BalanceSerializer
    required_permission = "wallets.view_balance"
    lookup_url_kwarg = "user_id"

    def get_object(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        balance, _ = Balance.objects.get_or_create(user=user)
        return balance


class WalletDepositView(PermissionMixin, generics.CreateAPIView):
    """Staff deposits cash into a user's wallet. Only staff with credit_balance permission can do this."""

    serializer_class = DepositSerializer
    required_permission = "wallets.credit_balance"

    def perform_create(self, serializer):
        user_id = self.kwargs.get("user_id")
        target_user = get_object_or_404(User, id=user_id)
        serializer.save(target_user=target_user)


class WalletWithdrawView(PermissionMixin, APIView):
    """Withdraw funds from a user's wallet. Currently not implemented."""

    required_permission = "wallets.debit_balance"

    def post(self, request, user_id):
        return Response({"detail": "Withdraw functionality not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Wallet Transactions
class WalletTransactionListView(VerifiedOwnerMixin, generics.ListAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_transaction"

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            return Transaction.objects.filter(balance=balance)
        except Balance.DoesNotExist:
            return Transaction.objects.none()


class WalletTransactionDetailView(VerifiedOwnerMixin, generics.RetrieveAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_transaction"

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            return Transaction.objects.filter(balance=balance)
        except Balance.DoesNotExist:
            return Transaction.objects.none()
