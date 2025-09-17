from decimal import Decimal

from rest_framework import serializers

from apps.common.constants import TransactionType
from apps.wallets.models import Balance, Transaction
from apps.wallets.services import WalletError, deposit


# ---------------------------
# Read-only wallet snapshot
# ---------------------------
class BalanceSerializer(serializers.ModelSerializer):
    """Read-only snapshot of a user's wallet."""

    available_balance = serializers.SerializerMethodField()

    class Meta:
        model = Balance
        fields = ["current_balance", "on_hold", "available_balance"]
        read_only_fields = fields

    def get_available_balance(self, obj):
        return obj.current_balance - obj.on_hold


# ---------------------------
# Internal transaction record
# ---------------------------
class TransactionSerializer(serializers.ModelSerializer):
    """Read-only transaction record."""

    class Meta:
        model = Transaction
        fields = ["id", "type", "amount", "remaining_balance", "created_at", "order"]
        read_only_fields = fields


# ---------------------------
# Customer-facing transaction
# ---------------------------
class TransactionPublicSerializer(serializers.ModelSerializer):
    """Customer-facing transaction record."""

    signed_amount = serializers.SerializerMethodField()
    label = serializers.SerializerMethodField()
    order_no = serializers.CharField(source="order.order_no", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "signed_amount",
            "amount",
            "remaining_balance",
            "order_no",
            "created_at",
        ]
        read_only_fields = fields

    def get_signed_amount(self, obj) -> Decimal:
        if obj.type == TransactionType.PAYMENT:
            return -obj.amount
        return obj.amount

    def get_label(self, obj) -> str:
        if obj.type == TransactionType.DEPOSIT:
            return "Cash Deposit"
        if obj.type == TransactionType.PAYMENT:
            return f"Payment for order {getattr(obj.order, 'order_no', '-')}"
        if obj.type == TransactionType.REFUND:
            return f"Refund for order {getattr(obj.order, 'order_no', '-')}"
        return obj.type


# ---------------------------
# Deposit input + creation
# ---------------------------
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

    def create(self, validated_data):
        user = self.context["request"].user
        try:
            result = deposit(user, validated_data["amount"])
        except WalletError as err:
            raise serializers.ValidationError(str(err)) from err

        return result.transaction
