from django.db import models

from apps.common.models import BaseModel
from apps.menus.models import Menu, MenuItem
from apps.users.models import User


class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PREPARING = "preparing", "Preparing"
    PAID = "paid", "Paid"
    COMPLETED = "completed", "Completed"
    CANCELLED = "cancelled", "Cancelled"


class Order(BaseModel):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        db_column="user_id",
    )
    menu = models.ForeignKey(
        Menu,
        on_delete=models.PROTECT,
        related_name="orders",
        db_column="menu_id",
    )
    order_no = models.CharField(max_length=6, unique=True)  # for ex "ORD001"
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reservation_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "order"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["menu"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.order_no} • {self.user}"


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        db_column="order_id",
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name="order_items",
        db_column="menu_item_id",
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "order_item"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["menu_item"]),
        ]

    def __str__(self):
        return f"{self.order.order_no} · {self.menu_item.item.name} × {self.quantity}"
