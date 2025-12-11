from decimal import Decimal

from rest_framework import serializers

from apps.common.constants import TransactionType
from apps.orders.models import Order
from apps.wallets.models import Balance, Transaction
from apps.wallets.services import WalletError, capture_payment_by_staff, deposit, refund_payment_by_staff


class BalanceSerializer(serializers.ModelSerializer):
    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = Balance
        fields = ["current_balance", "on_hold", "available_balance"]
        read_only_fields = fields

    def get_available_balance(self, obj):
        return obj.current_balance - obj.on_hold


class TransactionPublicSerializer(serializers.ModelSerializer):
    signed_amount = serializers.SerializerMethodField()
    order_no = serializers.CharField(source="order.order_no", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",  # Transaction ID
            "type",  # deposit/payment/refund/hold
            "amount",  # Raw amount value
            "signed_amount",  # Amount with +/-
            "status",  # Transaction status (pending/completed/cancelled)
            "order_no",  # Order reference when available
            "remaining_balance",  # Balance after transaction
            "created_at",  # Transaction timestamp
        ]
        read_only_fields = fields

    def get_signed_amount(self, obj):
        if obj.type in [TransactionType.PAYMENT, TransactionType.HOLD]:
            return -obj.amount
        return obj.amount


class DepositSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        max_value=Decimal("10000.00"),
        write_only=True,
    )

    class Meta:
        model = Transaction
        fields = ["id", "amount", "type", "remaining_balance", "created_at", "order"]
        read_only_fields = ["id", "type", "remaining_balance", "created_at", "order"]

    def validate_amount(self, value: Decimal):
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        if value > Decimal("10000.00"):
            raise serializers.ValidationError("Maximum deposit amount is 10000.00.")
        return value

    def create(self, validated_data):
        target_user = validated_data.pop("target_user", None)
        user = target_user or self.context["request"].user
        try:
            result = deposit(user, validated_data["amount"])
        except WalletError as err:
            raise serializers.ValidationError(str(err)) from err

        return result.transaction


class BaseOrderTransactionSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(write_only=True, required=False)
    order_no = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount",
            "remaining_balance",
            "created_at",
            "order_id",
            "order_no",
        ]
        read_only_fields = ["id", "type", "amount", "remaining_balance", "created_at"]

    def get_order_queryset(self):
        return Order.objects.all()

    def validate(self, attrs):
        order_id = attrs.get("order_id")
        order_no = attrs.get("order_no")

        # Require exactly one parameter (not both, not none)
        if not order_id and not order_no:
            raise serializers.ValidationError("Provide either 'order_id' or 'order_no' (not both).")

        if order_id and order_no:
            raise serializers.ValidationError("Provide either 'order_id' or 'order_no' (not both).")

        # Find the order
        qs = self.get_order_queryset()
        try:
            order = qs.get(id=order_id) if order_id else qs.get(order_no=order_no)
        except Order.DoesNotExist as err:
            raise serializers.ValidationError("Order not found.") from err

        attrs["order"] = order
        return attrs


class CapturePaymentSerializer(BaseOrderTransactionSerializer):
    def create(self, validated_data):
        user = self.context["request"].user
        order = validated_data["order"]
        try:
            result = capture_payment_by_staff(user=user, order_id=order.id)
        except WalletError as err:
            raise serializers.ValidationError(str(err)) from err
        return result.transaction


class RefundPaymentSerializer(BaseOrderTransactionSerializer):
    def create(self, validated_data):
        user = self.context["request"].user
        order = validated_data["order"]
        try:
            result = refund_payment_by_staff(user=user, order_id=order.id)
        except WalletError as err:
            raise serializers.ValidationError(str(err)) from err
        return result.transaction


class CreateCheckoutSessionSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal("0.01"),
        required=True,
        help_text="Amount to top up in dollars (e.g., 50.00)",
    )
    currency = serializers.CharField(
        max_length=3,
        default="mdl",
        required=False,
        help_text="Currency code (e.g., mdl, usd, eur)",
    )

    def validate_amount(self, value: Decimal):
        from django.conf import settings

        if value < settings.STRIPE_MIN_TOP_UP:
            raise serializers.ValidationError(f"Minimum top-up amount is {settings.STRIPE_MIN_TOP_UP}")
        if value > settings.STRIPE_MAX_TOP_UP:
            raise serializers.ValidationError(f"Maximum top-up amount is {settings.STRIPE_MAX_TOP_UP}")
        return value

    def validate_currency(self, value: str):
        value = value.lower()
        # Add more currencies as needed
        allowed_currencies = ["usd", "eur", "gbp", "mdl"]
        if value not in allowed_currencies:
            raise serializers.ValidationError(f"Currency must be one of: {', '.join(allowed_currencies)}")
        return value


class CheckoutSessionResponseSerializer(serializers.Serializer):
    session_id = serializers.CharField(read_only=True, help_text="Stripe checkout session ID")
    client_secret = serializers.CharField(read_only=True, help_text="Client secret for embedded checkout")
    amount = serializers.CharField(read_only=True, help_text="Top-up amount")
    currency = serializers.CharField(read_only=True, help_text="Currency code")
    transaction_id = serializers.UUIDField(read_only=True, help_text="Database transaction ID")


class SessionStatusResponseSerializer(serializers.Serializer):
    status = serializers.CharField(read_only=True, help_text="Session status (open, complete, expired)")
    payment_status = serializers.CharField(read_only=True, help_text="Payment status (paid, unpaid)")
    amount_total = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True, help_text="Total amount in dollars"
    )
    currency = serializers.CharField(read_only=True, help_text="Currency code")
    customer_email = serializers.EmailField(read_only=True, allow_null=True, help_text="Customer email if provided")
    transaction_status = serializers.CharField(read_only=True, allow_null=True, help_text="Database transaction status")
