from django.conf import settings
from django.db import models
from django.db.models import Q

from apps.common.models import BaseModel
from apps.orders.models import Order


class Balance(BaseModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="balance",
        db_column="user_id",
    )
    current_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    on_hold = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "balance"
        indexes = [models.Index(fields=["user"])]

    def __str__(self):
        return f"{self.user} • {self.current_balance} (hold {self.on_hold})"


class TransactionType(models.TextChoices):
    DEPOSIT = "deposit", "Deposit"
    PAYMENT = "payment", "Payment"
    REFUND = "refund", "Refund"
    # ADJUSTMENT = "adjustment", "Adjustment"


class Transaction(BaseModel):
    balance = models.ForeignKey(
        Balance,
        on_delete=models.CASCADE,
        related_name="wallets",
        db_column="balance_id",
    )
    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="wallets",
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
