import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from apps.common.mixins import PermissionMixin, VerifiedCustomerMixin
from apps.users.models import User
from apps.wallets.models import Balance, Transaction
from apps.wallets.serializers import (
    BalanceSerializer,
    CheckoutSessionResponseSerializer,
    CreateCheckoutSessionSerializer,
    DepositSerializer,
    SessionStatusResponseSerializer,
    TransactionPublicSerializer,
)
from apps.wallets.services import StripeService, WalletError


class _MeMixin(VerifiedCustomerMixin):
    def _bind_me(self, request):
        self.kwargs["user_id"] = request.user.id


# Wallet
@extend_schema(
    summary="Staff: Get user wallet balance",
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
    tags=["wallets"],
)
class WalletView(PermissionMixin, generics.RetrieveAPIView):
    serializer_class = BalanceSerializer
    required_permission = "wallets.view_all_balances"
    lookup_url_kwarg = "user_id"

    def get_object(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        balance, _ = Balance.objects.get_or_create(user=user)
        return balance


@extend_schema(
    summary="Staff: Deposit money into wallet",
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
    tags=["wallets"],
)
class WalletDepositView(PermissionMixin, generics.CreateAPIView):
    serializer_class = DepositSerializer
    required_permission = "wallets.credit_balance"

    def perform_create(self, serializer):
        user_id = self.kwargs.get("user_id")
        target_user = get_object_or_404(User, id=user_id)
        serializer.save(target_user=target_user)


# Wallet Transactions
@extend_schema(
    summary="Staff: Get transaction history",
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
    tags=["wallets"],
)
class WalletTransactionListView(PermissionMixin, generics.ListAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_all_transactions"

    def get_queryset(self):
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            return Transaction.objects.filter(balance=balance).select_related("order")
        except Balance.DoesNotExist:
            return Transaction.objects.none()


@extend_schema(
    summary="Staff: Get single transaction details",
    description="Get detailed information about a specific transaction",
    responses={200: TransactionPublicSerializer},
    tags=["wallets"],
)
class WalletTransactionDetailView(PermissionMixin, generics.RetrieveAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_all_transactions"

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
    summary="Customer: Get my wallet balance",
    description="Returns the authenticated & verified customer's wallet snapshot: current balance, on-hold,available.",
    operation_id="wallet_me_balance_retrieve",
    parameters=[],
    responses={200: BalanceSerializer},
    tags=["wallets"],
)
class WalletDetailMeView(_MeMixin, generics.RetrieveAPIView):
    serializer_class = BalanceSerializer
    required_permission = "wallets.view_own_balance"
    lookup_url_kwarg = None

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        self._bind_me(self.request)
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        balance, _ = Balance.objects.get_or_create(user=user)
        return balance


@extend_schema(
    summary="Customer: Get my wallet transactions",
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
    tags=["wallets"],
    examples=[
        OpenApiExample(
            "Transaction item",
            value={"id": 42, "type": "DEPOSIT", "amount": "50.00", "remaining_balance": "120.00", "order_no": None},
        )
    ],
)
class WalletTransactionsMeView(_MeMixin, generics.ListAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_own_transaction"
    lookup_url_kwarg = None

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        self._bind_me(self.request)
        user_id = self.kwargs.get("user_id")
        user = get_object_or_404(User, id=user_id)
        try:
            balance = Balance.objects.get(user=user)
            return Transaction.objects.filter(balance=balance).select_related("order")
        except Balance.DoesNotExist:
            return Transaction.objects.none()


@extend_schema(
    summary="Customer: Get my transaction details",
    description="Details for a specific transaction belonging to the authenticated & verified customer.",
    operation_id="wallet_me_transaction_retrieve",
    parameters=[
        OpenApiParameter(
            name="id", description="Transaction ID", required=True, type=str, location=OpenApiParameter.PATH
        ),
    ],
    responses={200: TransactionPublicSerializer},
    tags=["wallets"],
)
class WalletTransactionDetailMeView(_MeMixin, generics.RetrieveAPIView):
    serializer_class = TransactionPublicSerializer
    required_permission = "wallets.view_own_transaction"
    lookup_url_kwarg = None

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        self._bind_me(self.request)
        user_id = self.kwargs.get("user_id")
        transaction_id = self.kwargs.get("id")

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


logger = logging.getLogger(__name__)


@extend_schema(
    summary="Customer: Create Stripe checkout session",
    description="Create a Stripe embedded checkout session for wallet top-up. "
    "Returns client_secret to initialize Stripe.js on frontend.",
    request=CreateCheckoutSessionSerializer,
    responses={
        200: CheckoutSessionResponseSerializer,
        400: {"description": "Invalid amount or validation error"},
    },
    tags=["wallets", "stripe"],
)
class CreateCheckoutSessionView(VerifiedCustomerMixin, generics.CreateAPIView):
    serializer_class = CreateCheckoutSessionSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            stripe_service = StripeService()
            session_data = stripe_service.create_checkout_session(
                user=request.user,
                amount=serializer.validated_data["amount"],
                currency=serializer.validated_data.get("currency", "mdl"),
            )

            response_serializer = CheckoutSessionResponseSerializer(session_data)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except WalletError as e:
            logger.error(f"Stripe checkout error for user {request.user.id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="Customer: Check checkout session status",
    description="Retrieve the status of a Stripe checkout session and associated transaction.",
    parameters=[
        {
            "name": "session_id",
            "in": "query",
            "required": True,
            "schema": {"type": "string"},
            "description": "Stripe checkout session ID",
        }
    ],
    responses={
        200: SessionStatusResponseSerializer,
        400: {"description": "Missing or invalid session_id"},
        404: {"description": "Session not found"},
    },
    tags=["wallets", "stripe"],
)
class SessionStatusView(VerifiedCustomerMixin, generics.GenericAPIView):
    serializer_class = SessionStatusResponseSerializer

    def get(self, request, *args, **kwargs):
        session_id = request.query_params.get("session_id")

        if not session_id:
            return Response({"error": "session_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            stripe_service = StripeService()

            # Get Stripe session status
            session_status = stripe_service.retrieve_session_status(session_id)

            # Get local transaction status
            try:
                transaction = stripe_service.get_transaction_by_session(session_id)
                session_status["transaction_status"] = transaction.status
            except Exception:  # noqa
                session_status["transaction_status"] = None

            response_serializer = SessionStatusResponseSerializer(session_status)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except WalletError as e:
            logger.error(f"Failed to retrieve session status for {session_id}: {e}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
