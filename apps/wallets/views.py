from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.mixins import PermissionMixin, VerifiedCustomerMixin, VerifiedOwnerMixin
from apps.users.models import User
from apps.wallets.models import Balance, Transaction
from apps.wallets.serializers import (
    BalanceSerializer,
    DepositSerializer,
    TransactionPublicSerializer,
)


class _MeMixin(VerifiedCustomerMixin):
    def _bind_me(self, request):
        self.kwargs["user_id"] = request.user.id


# Wallet
@extend_schema(
    summary="Get user wallet balance",
    description="Get current wallet balance, on-hold amount, and available balance for the main wallet.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            description="User ID to get wallet balance for",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        )
    ],
    responses={200: BalanceSerializer},
    tags=["Wallets"],
)
class WalletView(VerifiedOwnerMixin, generics.RetrieveAPIView):
    serializer_class = BalanceSerializer
    required_permission = "wallets.view_balance"
    lookup_url_kwarg = "user_id"

    def get_object(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        balance, _ = Balance.objects.get_or_create(user=user)
        return balance


@extend_schema(
    summary="Deposit money into wallet",
    description="Staff deposits cash into a user's wallet. Creates a deposit transaction and updates the balance.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            description="User ID to deposit money into",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        )
    ],
    request=DepositSerializer,
    responses={201: DepositSerializer},
    tags=["Wallets"],
)
class WalletDepositView(PermissionMixin, generics.CreateAPIView):
    serializer_class = DepositSerializer
    required_permission = "wallets.credit_balance"

    def perform_create(self, serializer):
        user_id = self.kwargs.get("user_id")
        target_user = get_object_or_404(User, id=user_id)
        serializer.save(target_user=target_user)


class WalletWithdrawView(PermissionMixin, APIView):
    required_permission = "wallets.debit_balance"

    def post(self, request, user_id):
        return Response({"detail": "Withdraw functionality not implemented"}, status=status.HTTP_501_NOT_IMPLEMENTED)


# Wallet Transactions
@extend_schema(
    summary="Get transaction history",
    description="Get list: returns transaction history with ID, type, amount, status, order reference, and timestamps.",
    parameters=[
        OpenApiParameter(
            name="user_id",
            description="User ID to get transaction history for",
            required=True,
            type=str,
            location=OpenApiParameter.PATH,
        ),
        OpenApiParameter(
            name="page",
            description="Page number for pagination",
            required=False,
            type=int,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses={200: TransactionPublicSerializer(many=True)},
    tags=["Wallets"],
)
class WalletTransactionListView(VerifiedOwnerMixin, generics.ListAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_transaction"

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            return Transaction.objects.filter(balance=balance).select_related("order")
        except Balance.DoesNotExist:
            return Transaction.objects.none()


@extend_schema(
    summary="Get single transaction details",
    description="Get detailed information about a specific transaction",
    parameters=[
        OpenApiParameter(
            name="user_id", description="User ID", required=True, type=str, location=OpenApiParameter.PATH
        ),
        OpenApiParameter(
            name="pk", description="Transaction ID", required=True, type=int, location=OpenApiParameter.PATH
        ),
    ],
    responses={200: TransactionPublicSerializer},
    tags=["Wallets"],
)
class WalletTransactionDetailView(VerifiedOwnerMixin, generics.RetrieveAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_transaction"

    def get_object(self):
        user_id = self.kwargs.get("user_id")
        transaction_id = self.kwargs.get("pk")

        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            transaction = get_object_or_404(
                Transaction.objects.select_related("order"), balance=balance, id=transaction_id
            )
            return transaction
        except Balance.DoesNotExist as err:
            from django.http import Http404

            raise Http404("User has no wallet balance") from err


@extend_schema(
    summary="Get my wallet balance",
    description="Returns the authenticated & verified customer's wallet snapshot: current balance, on-hold,available.",
    operation_id="wallet_me_balance_retrieve",
    parameters=[],
    responses={200: BalanceSerializer},
    tags=["Wallets"],
)
class WalletDetailMeView(_MeMixin, generics.RetrieveAPIView):
    serializer_class = BalanceSerializer
    required_permission = "wallets.view_balance"
    lookup_url_kwarg = None

    def get(self, request, *args, **kwargs):
        self._bind_me(request)
        return super().get(request, *args, **kwargs)

    def get_object(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        balance, _ = Balance.objects.get_or_create(user=user)
        return balance


@extend_schema(
    summary="Get my wallet transactions",
    description="Paginated list of the authenticated & verified customer's transactions.",
    operation_id="wallet_me_transactions_list",
    parameters=[
        OpenApiParameter(
            name="page",
            description="Page number (pagination)",
            required=False,
            type=int,
            location=OpenApiParameter.QUERY,
        ),
    ],
    responses={200: TransactionPublicSerializer(many=True)},
    tags=["Wallets"],
    examples=[
        OpenApiExample(
            "Transaction item",
            value={"id": 42, "type": "DEPOSIT", "amount": "50.00", "remaining_balance": "120.00", "order_no": None},
        )
    ],
)
class WalletTransactionsMeView(_MeMixin, generics.ListAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_transaction"
    lookup_url_kwarg = None

    def get(self, request, *args, **kwargs):
        self._bind_me(request)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            return Transaction.objects.filter(balance=balance).select_related("order")
        except Balance.DoesNotExist:
            return Transaction.objects.none()


@extend_schema(
    summary="Get my transaction details",
    description="Details for a specific transaction belonging to the authenticated & verified customer.",
    operation_id="wallet_me_transaction_retrieve",
    parameters=[
        OpenApiParameter(
            name="pk", description="Transaction ID", required=True, type=int, location=OpenApiParameter.PATH
        ),
    ],
    responses={200: TransactionPublicSerializer},
    tags=["Wallets"],
)
class WalletTransactionDetailMeView(_MeMixin, generics.RetrieveAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_transaction"
    lookup_url_kwarg = None

    def get(self, request, *args, **kwargs):
        self._bind_me(request)
        return super().get(request, *args, **kwargs)

    def get_object(self):
        user_id = self.kwargs.get("user_id")
        transaction_id = self.kwargs.get("pk")

        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            transaction = get_object_or_404(
                Transaction.objects.select_related("order"), balance=balance, id=transaction_id
            )
            return transaction
        except Balance.DoesNotExist as err:
            from django.http import Http404

            raise Http404("User has no wallet balance") from err
