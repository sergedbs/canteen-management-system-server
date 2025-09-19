from decimal import Decimal

from rest_framework import serializers

from apps.common.constants import TransactionType
from apps.orders.models import Order
from apps.wallets.models import Balance, Transaction
from apps.wallets.services import WalletError, capture_payment_by_staff, deposit, refund_payment_by_staff


class BalanceSerializer(serializers.ModelSerializer):
    """Read-only snapshot of a user's wallet."""

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = Balance
        fields = ["current_balance", "on_hold", "available_balance"]
        read_only_fields = fields

    def get_available_balance(self, obj):
        return obj.current_balance - obj.on_hold


class TransactionPublicSerializer(serializers.ModelSerializer):
    """Customer-facing transaction record."""

    signed_amount = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    order_no = serializers.CharField(source="order.order_no", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",  # Transaction ID
            "type",  # deposit/payment/refund
            "amount",  # Raw amount value
            "signed_amount",  # Amount with +/-
            "status",  # Transaction status
            "order_no",  # Order reference when available
            "remaining_balance",  # Balance after transaction
            "created_at",  # Transaction timestamp
        ]
        read_only_fields = fields

    def get_signed_amount(self, obj):
        if obj.type == TransactionType.PAYMENT:
            return -obj.amount
        return obj.amount

    def get_status(self, obj):
        """Simple status logic"""
        if obj.type == TransactionType.DEPOSIT:
            return "completed"
        elif obj.type in [TransactionType.PAYMENT, TransactionType.REFUND]:
            if obj.order:
                return obj.order.status.lower()
            else:
                return "error"
        return "completed"


class DepositSerializer(serializers.ModelSerializer):
    """Staff takes cash and deposits it into the user's wallet."""

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
    """Model serializer that accepts either order_id or order_no"""

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

        if not order_id and not order_no:
            raise serializers.ValidationError("Provide either 'order_id' or 'order_no'.")

        qs = self.get_order_queryset()
        try:
            if order_id and order_no:
                order = qs.get(id=order_id)
                if order.order_no != order_no:
                    raise serializers.ValidationError("order_id and order_no refer to different orders.")
            elif order_id:
                order = qs.get(id=order_id)
            else:
                order = qs.get(order_no=order_no)
        except Order.DoesNotExist as err:
            raise serializers.ValidationError("Order not found.") from err

        return attrs


class CapturePaymentSerializer(BaseOrderTransactionSerializer):
    """Staff confirms pickup: capture from held funds. Creates a PAYMENT transaction."""

    def create(self, validated_data):
        user = self.context["request"].user
        order = validated_data["order"]
        try:
            result = capture_payment_by_staff(user=user, order_id=order.id)
        except WalletError as err:
            raise serializers.ValidationError(str(err)) from err
        return result.transaction


class RefundPaymentSerializer(BaseOrderTransactionSerializer):
    """Staff refunds a paid/completed order. Creates a REFUND transaction."""

    def create(self, validated_data):
        user = self.context["request"].user
        order = validated_data["order"]
        try:
            result = refund_payment_by_staff(user=user, order_id=order.id)
        except WalletError as err:
            raise serializers.ValidationError(str(err)) from err
        return result.transaction
