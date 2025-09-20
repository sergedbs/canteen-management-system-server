from django.db import models
from django.db.models import Q

from apps.common.constants import TransactionType
from apps.common.models import BaseModel
from apps.orders.models import Order
from apps.users.models import User


class Balance(BaseModel):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="balance",
        db_column="user_id",
    )
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    on_hold = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "balance"
        indexes = [models.Index(fields=["user"])]
        permissions = [
            ("credit_balance", "Can credit a user's balance"),
            ("debit_balance", "Can debit a user's balance"),
            ("view_all_balances", "Can view all user balances"),
            ("view_own_balance", "Can view own balance"),
        ]

    def __str__(self):
        return f"{self.user} • {self.current_balance} (hold {self.on_hold})"


class Transaction(BaseModel):
    balance = models.ForeignKey(
        Balance,
        on_delete=models.CASCADE,
        related_name="transactions",
        db_column="balance_id",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
        db_column="order_id",
    )
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "transaction"
        indexes = [
            models.Index(fields=["balance", "created_at"]),
            models.Index(fields=["type"]),
        ]
        ordering = ["-created_at"]
        permissions = [
            ("refund_payment", "Can create a refund for a payment"),
            ("view_all_transactions", "Can view all transactions"),
            ("view_own_transaction", "Can view own transactions"),
        ]

        constraints = [
            # Payments must be tied to an order
            models.CheckConstraint(
                name="payment_requires_order",
                check=~Q(type="payment") | Q(order__isnull=False),
            ),
            # Refunds must be tied to an order
            models.CheckConstraint(
                name="refund_requires_order",
                check=~Q(type="refund") | Q(order__isnull=False),
            ),
            # Deposits must NOT be tied to an order
            models.CheckConstraint(
                name="deposit_must_not_have_order",
                check=~Q(type="deposit") | Q(order__isnull=True),
            ),
        ]

    def __str__(self):
        ref = f" (order {self.order.order_no})" if self.order_id else ""
        return f"{self.type} {self.amount}{ref}"
